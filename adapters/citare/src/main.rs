//! citation-bench adapter for citare: JSONL requests on stdin, JSONL responses on stdout.
//! Speaks protocol version 2 (find, resolve, annotate); see docs/protocol.md in the
//! citation-bench repository.

use std::collections::HashMap;
use std::io::{self, BufRead, Write};

use citare_core::{
    annotate_citations, clean_text, get_citations, resolve_citations, Citation, CleanStep,
    UnbalancedTags,
};
use serde_json::{json, Map, Value};

fn neutral_type(name: &str) -> &'static str {
    match name {
        "FullCaseCitation" => "full_case",
        "ShortCaseCitation" => "short_case",
        "FullLawCitation" => "full_law",
        "FullJournalCitation" => "full_journal",
        "SupraCitation" => "supra",
        "IdCitation" => "id",
        "ReferenceCitation" => "reference",
        _ => "unknown",
    }
}

/// Map UTF-8 byte offsets in `text` to Unicode code point offsets.
fn code_points(text: &str, byte: usize) -> usize {
    text[..byte.min(text.len())].chars().count()
}

/// Run find over the request's input. Returns the citations and the text their byte
/// spans index: the input after clean steps.
fn find(req: &Value) -> Result<(Vec<Citation>, String), String> {
    let input = &req["input"];
    let text = input["text"].as_str().ok_or("input.text missing")?;
    let html = input["format"].as_str() == Some("html");
    let steps: Vec<CleanStep> = input["clean_steps"]
        .as_array()
        .into_iter()
        .flatten()
        .filter_map(|s| s.as_str().and_then(CleanStep::from_name))
        .collect();
    let remove_ambiguous = req["options"]["remove_ambiguous"]
        .as_bool()
        .unwrap_or(false);
    let cites = if html {
        get_citations("", remove_ambiguous, text, &steps)
    } else {
        get_citations(text, remove_ambiguous, "", &steps)
    };
    let cleaned = clean_text(text, &steps).unwrap_or_else(|_| text.to_string());
    Ok((cites, cleaned))
}

fn citation_json(c: &Citation, cleaned: &str) -> Value {
    let (start, end) = c.span();
    let (full_start, full_end) = c.full_span();
    let mut out = Map::new();
    out.insert("type".into(), json!(neutral_type(c.type_name())));
    out.insert(
        "span".into(),
        json!([code_points(cleaned, start), code_points(cleaned, end)]),
    );
    out.insert(
        "full_span".into(),
        json!([
            code_points(cleaned, full_start),
            code_points(cleaned, full_end)
        ]),
    );
    let groups: Map<String, Value> = c
        .common()
        .groups
        .iter()
        .filter_map(|(k, v)| v.as_ref().map(|v| (k.clone(), json!(v))))
        .collect();
    out.insert("groups".into(), Value::Object(groups));
    let metadata: Map<String, Value> = extract_metadata(c)
        .into_iter()
        .filter_map(|(k, v)| v.map(|v| (k, json!(v))))
        .collect();
    out.insert("metadata".into(), Value::Object(metadata));
    if let Some(rc) = c.resource_common() {
        out.insert("reporter_normalized".into(), json!(c.corrected_reporter()));
        out.insert("year".into(), json!(rc.year));
    }
    Value::Object(out)
}

/// For each citation in document order, the index of its resource group or null.
/// Groups are numbered by first appearance; citations are matched by span, since
/// citare's equality ignores position.
fn resolution(cites: &[Citation]) -> Vec<Option<usize>> {
    let mut group_of: HashMap<(usize, usize), usize> = HashMap::new();
    for (g, members) in resolve_citations(cites).values().enumerate() {
        for m in members {
            group_of.insert(m.span(), g);
        }
    }
    let mut seen: HashMap<usize, usize> = HashMap::new();
    cites
        .iter()
        .map(|c| {
            group_of.get(&c.span()).map(|g| {
                let next = seen.len();
                *seen.entry(*g).or_insert(next)
            })
        })
        .collect()
}

fn annotate(req: &Value, cites: &[Citation], cleaned: &str) -> Result<String, String> {
    let opts = &req["options"]["annotate"];
    let before = opts["before"]
        .as_str()
        .ok_or("options.annotate.before missing")?;
    let after = opts["after"]
        .as_str()
        .ok_or("options.annotate.after missing")?;
    let unbalanced = match opts["unbalanced_tags"].as_str().unwrap_or("unchecked") {
        "unchecked" => UnbalancedTags::Unchecked,
        "skip" => UnbalancedTags::Skip,
        "wrap" => UnbalancedTags::Wrap,
        other => return Err(format!("unknown unbalanced_tags {other:?}")),
    };
    let mut markers: Vec<((usize, usize), String, String)> = cites
        .iter()
        .enumerate()
        .map(|(i, c)| {
            let i = i.to_string();
            (
                c.span(),
                before.replace("{i}", &i),
                after.replace("{i}", &i),
            )
        })
        .collect();
    let source = req["input"]["text"].as_str().unwrap_or_default();
    Ok(annotate_citations(
        cleaned,
        &mut markers,
        source,
        unbalanced,
        None,
        None,
    ))
}

fn respond(req: &Value) -> Result<Map<String, Value>, String> {
    let (cites, cleaned) = find(req)?;
    let citations = || Value::Array(cites.iter().map(|c| citation_json(c, &cleaned)).collect());
    let mut out = Map::new();
    match req["kind"].as_str().unwrap_or("find") {
        "find" => {
            out.insert("citations".into(), citations());
        }
        "resolve" => {
            out.insert("citations".into(), citations());
            out.insert("resolution".into(), json!(resolution(&cites)));
        }
        "annotate" => {
            out.insert("text".into(), json!(annotate(req, &cites, &cleaned)?));
        }
        other => return Err(format!("unsupported kind {other:?}")),
    }
    Ok(out)
}

fn main() {
    // Build the tokenizer before the first timed request.
    get_citations("1 U.S. 1", false, "", &[]);
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        let line = line.expect("stdin");
        let req: Value = match serde_json::from_str(&line) {
            Ok(v) => v,
            Err(e) => {
                writeln!(out, "{}", json!({"id": null, "error": e.to_string()})).unwrap();
                continue;
            }
        };
        let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| respond(&req)));
        let res = match result {
            Ok(Ok(mut body)) => {
                body.insert("id".into(), req["id"].clone());
                Value::Object(body)
            }
            Ok(Err(e)) => json!({"id": req["id"], "error": e}),
            Err(_) => json!({"id": req["id"], "error": "panic"}),
        };
        writeln!(out, "{res}").unwrap();
        out.flush().unwrap();
    }
}

/// Flatten per-variant metadata structs into a uniform string map.
fn extract_metadata(citation: &citare_core::Citation) -> HashMap<String, Option<String>> {
    let mut map: HashMap<String, Option<String>> = HashMap::new();

    match citation {
        citare_core::Citation::FullCase(d) => {
            let m = &d.metadata;
            let c = &m.case;
            insert_opt(&mut map, "parenthetical", &c.parenthetical);
            insert_opt(&mut map, "pin_cite", &c.pin_cite);
            insert_opt(&mut map, "year", &c.year);
            insert_opt(&mut map, "month", &c.month);
            insert_opt(&mut map, "day", &c.day);
            insert_opt(&mut map, "court", &c.court);
            insert_opt(&mut map, "plaintiff", &m.plaintiff);
            insert_opt(&mut map, "defendant", &m.defendant);
            insert_opt(&mut map, "extra", &m.extra);
            insert_opt(&mut map, "antecedent_guess", &m.antecedent_guess);
            insert_opt(
                &mut map,
                "resolved_case_name_short",
                &m.resolved_case_name_short,
            );
            insert_opt(&mut map, "resolved_case_name", &m.resolved_case_name);
        }
        citare_core::Citation::ShortCase(d) => {
            let m = &d.metadata;
            let c = &m.case;
            insert_opt(&mut map, "parenthetical", &c.parenthetical);
            insert_opt(&mut map, "pin_cite", &c.pin_cite);
            insert_opt(&mut map, "year", &c.year);
            insert_opt(&mut map, "month", &c.month);
            insert_opt(&mut map, "day", &c.day);
            insert_opt(&mut map, "court", &c.court);
            insert_opt(&mut map, "antecedent_guess", &m.antecedent_guess);
        }
        citare_core::Citation::FullLaw(d) => {
            let m = &d.metadata;
            insert_opt(&mut map, "parenthetical", &m.parenthetical);
            insert_opt(&mut map, "pin_cite", &m.pin_cite);
            insert_opt(&mut map, "year", &m.year);
            insert_opt(&mut map, "month", &m.month);
            insert_opt(&mut map, "day", &m.day);
            insert_opt(&mut map, "publisher", &m.publisher);
        }
        citare_core::Citation::FullJournal(d) => {
            let m = &d.metadata;
            insert_opt(&mut map, "parenthetical", &m.parenthetical);
            insert_opt(&mut map, "pin_cite", &m.pin_cite);
            insert_opt(&mut map, "year", &m.year);
            insert_opt(&mut map, "month", &m.month);
            insert_opt(&mut map, "day", &m.day);
        }
        citare_core::Citation::Supra(d) => {
            let m = &d.metadata;
            insert_opt(&mut map, "parenthetical", &m.parenthetical);
            insert_opt(&mut map, "pin_cite", &m.pin_cite);
            insert_opt(&mut map, "antecedent_guess", &m.antecedent_guess);
            insert_opt(&mut map, "volume", &m.volume);
        }
        citare_core::Citation::Id(d) => {
            let m = &d.metadata;
            insert_opt(&mut map, "parenthetical", &m.parenthetical);
            insert_opt(&mut map, "pin_cite", &m.pin_cite);
        }
        citare_core::Citation::Reference(d) => {
            let m = &d.metadata;
            insert_opt(&mut map, "parenthetical", &m.parenthetical);
            insert_opt(&mut map, "pin_cite", &m.pin_cite);
            insert_opt(&mut map, "plaintiff", &m.plaintiff);
            insert_opt(&mut map, "defendant", &m.defendant);
            insert_opt(
                &mut map,
                "resolved_case_name_short",
                &m.resolved_case_name_short,
            );
            insert_opt(&mut map, "resolved_case_name", &m.resolved_case_name);
        }
        citare_core::Citation::Unknown(_) => {}
    }

    map
}

#[inline]
fn insert_opt(map: &mut HashMap<String, Option<String>>, key: &str, value: &Option<String>) {
    map.insert(key.to_string(), value.clone());
}
