"""bench/verify_statutes.py on small fixtures; no network."""

import hashlib
import json

import pytest
import verify_statutes as vs

USCODE_MODS = """<?xml version="1.0"?>
<mods xmlns="http://www.loc.gov/mods/v3">
 <relatedItem type="constituent" ID="id-USCODE-2024-title28-chap1-sec1">
  <identifier type="Parent Id">id-USCODE-2024-title28-chap1</identifier>
  <titleInfo><title>Number of justices</title><partName>Sec. 1</partName></titleInfo>
 </relatedItem>
 <relatedItem type="constituent" ID="id-USCODE-2024-title28-chap1-sec5">
  <identifier type="Parent Id">id-USCODE-2024-title28-chap1</identifier>
  <titleInfo><title>Repealed</title><partName>Secs. 5 to 7</partName></titleInfo>
 </relatedItem>
 <relatedItem type="constituent" ID="id-USCODE-2024-title28-app">
  <titleInfo><title>APPENDIX</title><partName>TITLE 28</partName></titleInfo>
 </relatedItem>
 <relatedItem type="constituent" ID="id-USCODE-2024-title28-app-federalru-dup1">
  <identifier type="Parent Id">id-USCODE-2024-title28-app</identifier>
  <titleInfo><title>FEDERAL RULES OF CIVIL PROCEDURE</title></titleInfo>
 </relatedItem>
 <relatedItem type="constituent" ID="id-USCODE-2024-title28-app-federalru-dup1-other">
  <identifier type="Parent Id">id-USCODE-2024-title28-app-federalru-dup1</identifier>
  <titleInfo><title>TITLE III. PLEADINGS AND MOTIONS</title></titleInfo>
 </relatedItem>
 <relatedItem type="constituent" ID="id-USCODE-2024-title28-app-federalru-dup1-rule12">
  <identifier type="Parent Id">id-USCODE-2024-title28-app-federalru-dup1-other</identifier>
  <titleInfo><title>Defenses</title><partName>Rule 12</partName></titleInfo>
 </relatedItem>
 <relatedItem type="constituent" ID="id-USCODE-2024-title28-app-federalru-dup1-supp">
  <identifier type="Parent Id">id-USCODE-2024-title28-app-federalru-dup1</identifier>
  <titleInfo><title>SUPPLEMENTAL RULES FOR SOCIAL SECURITY ACTIONS</title></titleInfo>
 </relatedItem>
 <relatedItem type="constituent" ID="id-USCODE-2024-title28-app-federalru-dup1-rule99-dup1">
  <identifier type="Parent Id">id-USCODE-2024-title28-app-federalru-dup1-supp</identifier>
  <titleInfo><title>Supplemental</title><partName>Rule 99</partName></titleInfo>
 </relatedItem>
</mods>
"""

STATUTE_MODS = """<?xml version="1.0"?>
<mods xmlns="http://www.loc.gov/mods/v3">
 <relatedItem type="constituent" ID="id-STATUTE-88-Pg829">
  <part type="article"><extent unit="pages"><start>829</start><end>1035</end></extent></part>
  <extension><accessId>STATUTE-88-Pg829</accessId><granuleDate>1974-09-02</granuleDate>
   <granuleClass>PUBLICLAW</granuleClass><congress>93</congress><number>406</number>
  </extension>
 </relatedItem>
 <relatedItem type="constituent" ID="id-STATUTE-88-PgA1">
  <part type="article"><extent unit="pages"><start>A1</start></extent></part>
  <extension><accessId>STATUTE-88-PgA1</accessId><congress>93</congress></extension>
 </relatedItem>
</mods>
"""

CONSTITUTION = r"""
                               Article I.

    Section 1. All legislative Powers herein granted shall be vested.

    Section 8. \1\The Congress shall have Power To lay and collect Taxes;
    \2\To borrow Money on the credit of the United States;
    \3\To regulate Commerce with foreign Nations;\7\

                              Article V.

    The Congress, whenever two thirds of both Houses shall deem it necessary.

                            Article [I.]\13\

    Congress shall make no law respecting an establishment of religion.

                              Article XIV.

    Section 1. All persons born or naturalized in the United States.
    Section 5. The Congress shall have power to enforce.
"""

LAWS = {
    "U.S.C.": [
        {"jurisdiction": "United States", "regexes": ["$reporter § $law_section"]}
    ],
    "N.C. Gen. Stat.": [
        {"jurisdiction": "North Carolina", "regexes": ["$reporter § $law_section"]}
    ],
    "N.Y. Law": [
        {
            "jurisdiction": "New York",
            "regexes": ["(?P<reporter>N\\.Y\\. $law_subject Law) § $law_section"],
        }
    ],
}

NC_PAGE = (
    "<html><body><p>G.S. 163-122</p><h1>§ 163-122. Unaffiliated candidates.</h1>"
    "<script>var x = '§ 999-1.';</script></body></html>"
)


def vector(vid, text, span, groups, code, jurisdiction, **metadata):
    return {
        "id": f"t/find/{vid}",
        "kind": "find",
        "source": {"corpus": "courtlistener-10pct", "opinion": "1", "offset": 0},
        "input": {"text": text, "format": "plain", "clean_steps": []},
        "expected": {
            "citations": [
                {
                    "type": "full_law",
                    "span": span,
                    "groups": groups,
                    "reporter_normalized": code,
                    "metadata": {"jurisdiction": jurisdiction, **metadata},
                }
            ]
        },
    }


def fake_opener(pages):
    calls = []

    def opener(url, follow):
        calls.append(url)
        if url not in pages:
            return 404, b"", None
        status, body, location = pages[url]
        return status, body.encode() if isinstance(body, str) else body, location

    opener.calls = calls
    return opener


def pages():
    return {
        "https://raw.githubusercontent.com/freelawproject/reporters-db/"
        f"{vs.REPORTERS_DB_TAG}/reporters_db/data/laws.json": (
            200,
            json.dumps(LAWS),
            None,
        ),
        f"https://www.govinfo.gov/metadata/pkg/USCODE-{vs.USCODE_EDITION}-title28/mods.xml": (
            200,
            USCODE_MODS,
            None,
        ),
        "https://www.govinfo.gov/content/pkg/CDOC-110hdoc50/html/CDOC-110hdoc50.htm": (
            200,
            CONSTITUTION,
            None,
        ),
        "https://www.ncleg.gov/EnactedLegislation/Statutes/HTML/BySection/Chapter_163/"
        "GS_163-122.html": (200, NC_PAGE, None),
    }


# --- parsers -----------------------------------------------------------------------


def test_uscode_mods_sections_and_rules():
    parsed = vs.parse_uscode_mods(USCODE_MODS.encode())
    assert {"1", "5", "5 to 7"} <= parsed["sections"]
    assert parsed["rules"] == {"FEDERAL RULES OF CIVIL PROCEDURE": {"12"}}


def test_statute_mods_skips_unnumbered_pages():
    parsed = vs.parse_statute_mods(STATUTE_MODS.encode())
    assert parsed["congresses"] == {"93"}
    assert [g["id"] for g in parsed["granules"]] == ["STATUTE-88-Pg829"]
    assert parsed["granules"][0]["end"] == 1035


def test_constitution_clauses_and_amendments():
    c = vs.parse_constitution(CONSTITUTION)
    assert c["article"][1] == {1: 0, 8: 3}  # footnote \7\ isn't a clause
    assert 5 in c["article"] and c["article"][5] == {}
    assert c["amendment"][1] == {}
    assert set(c["amendment"][14]) == {1, 5}


def test_roman_and_canonical():
    assert [vs.roman_to_int(r) for r in ("I", "IV", "VIII", "XIV", "XXVII")] == [
        1,
        4,
        8,
        14,
        27,
    ]
    assert vs.canonical("U.S.C.A.") == vs.canonical("U.S.C.") == "usc"
    assert vs.canonical("Tex. Penal Code Ann.") == vs.canonical("TEX. PENAL CODE")
    assert vs.stat_volumes(93) == [87, 88]


def test_page_text_drops_scripts():
    assert "999-1" not in vs.page_text(NC_PAGE.encode())


# --- span and metadata checks -------------------------------------------------------


def checks_for(v):
    return vs.span_checks(v["input"]["text"], v["expected"]["citations"][0])


def test_span_checks_pass():
    v = vector(
        "a",
        "See 28 U.S.C. § 1(a) (emphasis added).",
        [4, 17],
        {"title": "28", "reporter": "U.S.C.", "section": "1"},
        "U.S.C.",
        "United States",
        pin_cite="(a)",
        parenthetical="emphasis added",
    )
    assert [(c.claim, c.result) for c in checks_for(v)] == [
        ("span", "pass"),
        ("metadata", "pass"),
    ]


def test_span_taking_the_period_fails():
    v = vector(
        "b",
        "Pub.L. No. 93-233.",
        [0, 18],
        {"reporter": "Pub.L.", "title": "93-233"},
        "Pub. L.",
        "United States",
    )
    span = checks_for(v)[0]
    assert span.result == "fail" and "doesn't end at the title" in span.detail


def test_pin_cite_must_follow_the_span():
    v = vector(
        "c",
        "28 U.S.C. § 1 and (b)",
        [0, 13],
        {"title": "28", "reporter": "U.S.C.", "section": "1"},
        "U.S.C.",
        "United States",
        pin_cite="(b)",
    )
    md = next(c for c in checks_for(v) if c.claim == "metadata")
    assert md.result == "fail"


def test_unfielded_text_and_spaced_section_go_to_a_person():
    v = vector(
        "d",
        "Ala. Code 1975, § 10 -236b.",
        [0, 26],
        {"reporter": "Ala. Code", "section": "10 -236b"},
        "Ala. Code",
        "Alabama",
    )
    humans = [c.human for c in checks_for(v) if c.human]
    assert ("span", "in-span text not in any field: `####,`") in humans
    assert ("span", "whitespace inside a section (`10 -236b`)") in humans


# --- fetching and pinning ------------------------------------------------------------


def test_fetcher_caches_and_pins(tmp_path):
    opener = fake_opener({"https://x/a": (200, "hello", None)})
    f = vs.Fetcher(tmp_path, {}, opener=opener)
    assert f.get("https://x/a") == (200, b"hello")
    assert f.get("https://x/a") == (200, b"hello")
    assert opener.calls == ["https://x/a"]
    assert f.used["https://x/a"]["sha256"] == hashlib.sha256(b"hello").hexdigest()

    # A cached copy that isn't the pinned one is refused...
    lock = {"https://x/a": {"sha256": "0" * 64}}
    with pytest.raises(vs.SourceChanged):
        vs.Fetcher(tmp_path, lock, opener=opener).get("https://x/a")
    # ...and a source that changed upstream is used, repinned and reported.
    f = vs.Fetcher(tmp_path / "fresh", lock, opener=opener)
    assert f.get("https://x/a") == (200, b"hello")
    assert f.changed == {"https://x/a": "0" * 64}
    assert f.used["https://x/a"]["sha256"] == hashlib.sha256(b"hello").hexdigest()


def test_fetcher_offline_without_cache(tmp_path):
    with pytest.raises(vs.SourceUnavailable):
        vs.Fetcher(tmp_path, {}, offline=True).get("https://x/b")


def test_redirect_only_records_the_location(tmp_path):
    url = "https://www.govinfo.gov/link/fr/50/40293"
    loc = "https://www.govinfo.gov/content/pkg/FR-1985-10-02/pdf/FR-1985-10-02.pdf#page=119"
    f = vs.Fetcher(tmp_path, {}, opener=fake_opener({url: (302, "", loc)}))
    assert vs.Sources(f).fr_issue("50", "40293")[1:3] == ("pkg/FR-1985-10-02", "1985")


# --- verdicts end to end -------------------------------------------------------------


def write_set(tmp_path, vectors):
    d = tmp_path / "set"
    d.mkdir()
    (d / "SOURCE.json").write_text(
        json.dumps({"name": "t", "provenance": {"status": "proposed"}})
    )
    (d / "find.jsonl").write_text("".join(json.dumps(v) + "\n" for v in vectors))
    return d


def test_verdicts(tmp_path):
    vectors = [
        vector(
            "rule",
            "Fed.R.Civ.P. 12(b)(6).",
            [0, 15],
            {"reporter": "Fed.R.Civ.P.", "rule": "12"},
            "Fed. R. Civ. P.",
            "United States",
            pin_cite="(b)(6)",
        ),
        vector(
            "no_rule",
            "Fed. R. Civ. P. 99.",
            [0, 18],
            {"reporter": "Fed. R. Civ. P.", "rule": "99"},
            "Fed. R. Civ. P.",
            "United States",
        ),
        vector(
            "const",
            "U.S. Const. art. I, § 8, cl. 3.",
            [0, 23],
            {"reporter": "U.S. Const.", "article": "I", "section": "8"},
            "U.S. Const.",
            "United States",
            pin_cite="cl. 3",
        ),
        vector(
            "const_clause",
            "U.S. Const. art. I, § 8, cl. 4.",
            [0, 23],
            {"reporter": "U.S. Const.", "article": "I", "section": "8"},
            "U.S. Const.",
            "United States",
            pin_cite="cl. 4",
        ),
        vector(
            "nc",
            "See G.S. § 163-122.",
            [4, 18],
            {"reporter": "G.S.", "section": "163-122"},
            "N.C. Gen. Stat.",
            "North Carolina",
        ),
        vector(
            "ny",
            "Penal Law § 70.06.",
            [0, 17],
            {"reporter": "Penal Law", "section": "70.06", "subject": "Penal"},
            "N.Y. Penal Law",
            "New York",
        ),
    ]
    opener = fake_opener(pages())
    f = vs.Fetcher(tmp_path / "cache", {}, opener=opener)
    results = {
        r["id"].split("/")[-1]: r for r in vs.run([write_set(tmp_path, vectors)], f)
    }
    assert results["rule"]["verdict"].startswith(
        "verified-by-source:govinfo-uscode-2024"
    )
    assert results["no_rule"]["verdict"].startswith(
        "contradicted:existence: no Rule 99"
    )
    assert results["const"]["verdict"].startswith("verified-by-source:gpo-constitution")
    assert "has 3 clauses, not 4" in results["const_clause"]["verdict"]
    assert results["nc"]["verdict"] == (
        f"verified-by-source:ncleg+reporters-db@{vs.REPORTERS_DB_TAG}"
    )
    assert results["ny"]["verdict"] == "unverifiable:existence, form"

    _by, human = vs.summarize(list(results.values()))
    assert list(human["form"]) == ["`Penal Law` means `N.Y. Penal Law` (New York)"]
    md = vs.markdown(list(results.values()), f.used)
    assert "| **all** | 6 | 3 | 2 | 1 |" in md
