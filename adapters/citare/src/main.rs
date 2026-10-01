//! citation-bench adapter for citare: JSONL requests on stdin, JSONL responses on stdout.
//! See docs/protocol.md in the citation-bench repository.

use std::collections::HashMap;
use std::io::{self, BufRead, Write};

use citare_core::{clean_text, get_citations, CleanStep};
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

fn respond(req: &Value) -> Result<Vec<Value>, String> {
    let input = &req["input"];
    let text = input["text"].as_str().ok_or("input.text missing")?;
    let html = input["format"].as_str() == Some("html");
    let steps = || -> Vec<CleanStep> {
        input["clean_steps"]
            .as_array()
            .into_iter()
            .flatten()
            .filter_map(|s| s.as_str().and_then(CleanStep::from_name))
            .collect()
    };
    let remove_ambiguous = req["options"]["remove_ambiguous"].as_bool().unwrap_or(false);
    let cites = if html {
        get_citations("", remove_ambiguous, text, &steps())
    } else {
        get_citations(text, remove_ambiguous, "", &steps())
    };
    // Spans index the cleaned text, so convert offsets against that.
    let cleaned = clean_text(if html { "" } else { text }, &steps()).unwrap_or_default();

    Ok(cites
        .iter()
        .map(|c| {
            let (start, end) = c.span();
            let mut out = Map::new();
            out.insert("type".into(), json!(neutral_type(c.type_name())));
            out.insert(
                "span".into(),
                json!([code_points(&cleaned, start), code_points(&cleaned, end)]),
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
        })
        .collect())
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
            Ok(Ok(citations)) => json!({"id": req["id"], "citations": citations}),
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
            insert_opt(&mut map, "resolved_case_name_short", &m.resolved_case_name_short);
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
            insert_opt(&mut map, "resolved_case_name_short", &m.resolved_case_name_short);
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
