"""bench/verify_statutes.py on small fixtures; no network."""

import hashlib
import io
import json
import zipfile

import pytest
import verify_statutes as vs


@pytest.fixture(autouse=True)
def no_api_keys(monkeypatch):
    """The operator's env may hold the keys; tests set them only where they need them."""
    monkeypatch.delenv(vs.COURTLISTENER_TOKEN_ENV, raising=False)
    monkeypatch.delenv(vs.NY_OPENLEG_KEY_ENV, raising=False)


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

    def opener(url, follow, headers=None, data=None):
        calls.append(url)
        key = (url, data) if data else url
        if key not in pages:
            return 404, b"", None
        status, body, location = pages[key]
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


# --- sources that need a lookup or a PDF ----------------------------------------------


def cite(groups, code, jurisdiction="X"):
    return {
        "type": "full_law",
        "span": [0, 1],
        "groups": groups,
        "reporter_normalized": code,
        "metadata": {"jurisdiction": jurisdiction},
    }


def existence(page_map, groups, code, tmp_path, monkeypatch=None):
    if monkeypatch is not None:
        # PDF fixtures are plain text after a %PDF marker; pypdf isn't needed here.
        monkeypatch.setattr(vs, "pdf_text", lambda body: body.decode()[9:])
    f = vs.Fetcher(tmp_path / "cache", {}, opener=fake_opener(page_map))
    return vs.existence_check(vs.Sources(f), cite(groups, code))


def pdf(text):
    return b"%PDF-1.7\n" + text.encode()


LAW_SECTION_ROWS = (
    "`PEN1385.1`\t`PEN`\t`1385.`\t`1970`\tNULL\tNULL\tNULL\t`id`\tNULL\tNULL\tNULL"
    "\tNULL\tNULL\t`Added`\tLAW_SECTION_TBL_1.lob\t`Y`\t`LEG`\t2026-09-26\n"
    "`PEN9.1`\t`PEN`\t`9.`\t`1970`\tNULL\tNULL\tNULL\t`id`\tNULL\tNULL\tNULL"
    "\tNULL\tNULL\t`Repealed`\tLAW_SECTION_TBL_2.lob\t`N`\t`LEG`\t2026-09-26\n"
)


def pubinfo_prefix():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("BILL_TBL.dat", "bills\n" * 100)
        z.writestr("LAW_SECTION_TBL.dat", LAW_SECTION_ROWS)
        z.writestr("LAW_TOC_TBL.dat", "toc\n")
    return buf.getvalue()[:-40]  # a prefix: the central directory is cut off


def test_zip_member_and_california_rows():
    data = vs.zip_member(pubinfo_prefix(), "LAW_SECTION_TBL.dat")
    assert vs.parse_ca_law_sections(data) == {"PEN": {"1385"}}  # inactive row dropped
    with pytest.raises(vs.SourceUnavailable):
        vs.zip_member(pubinfo_prefix(), "NOT_THERE.dat")


def test_california_from_the_pubinfo_prefix(tmp_path):
    url = f"https://downloads.leginfo.legislature.ca.gov/pubinfo_{vs.CA_PUBINFO}.zip"
    pages = {url: (206, pubinfo_prefix(), None)}
    ok = existence(pages, {"section": "1385"}, "Cal. Pen. Code", tmp_path)
    assert ok.result == "pass" and ok.source.startswith("ca-leginfo-pubinfo")
    bad = existence(pages, {"section": "9"}, "Cal. Pen. Code", tmp_path / "b")
    assert bad.result == "fail"


def test_range_requests_are_pinned_under_their_own_key(tmp_path):
    f = vs.Fetcher(tmp_path, {}, opener=fake_opener({"https://x/z": (206, "ab", None)}))
    f.get("https://x/z", key="https://x/z#bytes=0-1", headers={"Range": "bytes=0-1"})
    assert f.used["https://x/z#bytes=0-1"]["url"] == "https://x/z"
    assert "https://x/z" not in f.used


CT_TITLE = (
    '<td><a class="toc_ch_link" href="chap_950.htm">Chapter 950</a> '
    '<span class="toc_rng_secs">Secs. 53a-1 to 53a-3</span></td>'
    '<td><a class="toc_ch_link" href="chap_951.htm">Chapter 951</a> '
    '<span class="toc_rng_secs">Secs. 53a-4 to 53a-23</span></td>'
    '<td><a class="toc_ch_link" href="chap_951a.htm">Chapter 951a</a> '
    '<span class="toc_rng_secs">Sec. 53a-23a</span></td>'
)
CT_CHAPTER = (
    '<p><span class="catchln" id="sec_53a-21">Sec. 53a-21. Use of physical force '
    "in defense of property.</span> A person is justified...</p>"
)


def test_connecticut_title_ranges():
    rows = vs.parse_ct_title(CT_TITLE)
    assert rows[1] == ("chap_951.htm", "53a-4", "53a-23")
    assert rows[2] == ("chap_951a.htm", "53a-23a", "53a-23a")
    assert vs.ct_title_file("1") == "01" and vs.ct_title_file("17a") == "17a"
    assert vs.section_key("101k") > vs.section_key("101") > vs.section_key("99z")


def test_connecticut_section(tmp_path):
    pages = {
        "https://www.cga.ct.gov/current/pub/title_53a.htm": (200, CT_TITLE, None),
        "https://www.cga.ct.gov/current/pub/chap_951.htm": (200, CT_CHAPTER, None),
    }
    assert existence(
        pages, {"section": "53a-21"}, "Conn. Gen. Stat.", tmp_path
    ).result == ("pass")
    # in chapter 951's range, but not on the page
    gone = existence(pages, {"section": "53a-22"}, "Conn. Gen. Stat.", tmp_path / "b")
    assert gone.result == "fail"
    beyond = existence(
        pages, {"section": "53a-400"}, "Conn. Gen. Stat.", tmp_path / "c"
    )
    assert beyond.result == "fail" and "no chapter" in beyond.detail


HI_INDEX = (
    '<A HREF="/hrscurrent/Vol05_Ch0261-0319/">Vol05_Ch0261-0319</A><br>'
    '<A HREF="/hrscurrent/Vol14_Ch0701-0853/">Vol14_Ch0701-0853</A><br>'
)


def test_hawaii_section_page(tmp_path):
    base = "https://data.capitol.hawaii.gov/hrscurrent/"
    pages = {
        base: (200, HI_INDEX, None),
        base + "Vol05_Ch0261-0319/HRS0291E/HRS_0291E-0021.htm": (
            200,
            "<p>&nbsp;<b>§291E-21&nbsp; Restitution.</b></p>",
            None,
        ),
    }
    ok = existence(pages, {"section": "291E-21"}, "Haw. Rev. Stat.", tmp_path)
    assert ok.result == "pass" and ok.source == "hawaii-legislature"
    missing = existence(
        pages, {"section": "707-999.5"}, "Haw. Rev. Stat.", tmp_path / "b"
    )
    assert missing.result == "fail" and "HRS_0707-0999_0005.htm" in missing.detail


def vt_chapter_page(chapter, sections):
    return "".join(
        f'<a href="/statutes/section/24/{chapter}/{s.zfill(5)}">  § {s}. Heading</a>'
        for s in sections
    )


def test_vermont_bisects_the_chapters(tmp_path):
    base = "https://legislature.vermont.gov/statutes/"
    chapters = {
        "001": ["1", "2"],
        "005": [],  # a chapter whose sections are all repealed
        "061": ["2201", "2202"],
        "117": ["4301", "4469", "4498"],
        "121": ["4601"],
    }
    pages = {
        base + "title/24": (
            200,
            "".join(
                f'<a href="/statutes/chapter/24/{c}">Chapter {c}</a>' for c in chapters
            ),
            None,
        ),
        **{
            base + f"chapter/24/{c}": (200, vt_chapter_page(c, s), None)
            for c, s in chapters.items()
        },
    }
    ok = existence(
        pages, {"title": "24", "section": "4469"}, "Vt. Stat. Ann.", tmp_path
    )
    assert ok.result == "pass" and ok.detail.endswith("chapter/24/117")
    gone = existence(
        pages, {"title": "24", "section": "4407"}, "Vt. Stat. Ann.", tmp_path / "b"
    )
    assert gone.result == "fail" and "inside chapter 117" in gone.detail
    between = existence(
        pages, {"title": "24", "section": "4550"}, "Vt. Stat. Ann.", tmp_path / "c"
    )
    assert between.result == "none"


def test_north_dakota_chapter_pdf(tmp_path, monkeypatch):
    url = "https://ndlegis.gov/cencode/t19c03-4.pdf"
    text = (
        "CHAPTER 19-03.4\n19-03.4-02. Definitions.\nSee section 19-03.4-03.\n"
        "19-03.4-03. Unlawful possession of drug paraphernalia - Penalty.\n"
    )
    pages = {url: (200, pdf(text), None)}
    ok = existence(
        pages, {"section": "19-03.4-03"}, "N.D. Cent. Code", tmp_path, monkeypatch
    )
    assert ok.result == "pass"
    no = existence(
        pages, {"section": "19-03.4-09"}, "N.D. Cent. Code", tmp_path / "b", monkeypatch
    )
    assert no.result == "fail"


def test_new_mexico_chapter_document(tmp_path, monkeypatch):
    base = "https://nmonesource.com/nmos/nmsa-unanno/en/"
    pages = {
        base + "nav_date.do?iframe=true": (
            200,
            (
                '<a href="/nmos/nmsa-unanno/en/item/18532/index.do">Chapter 32A - Code</a>'
                '<a href="/nmos/nmsa/en/nav_date.do?page=2">2</a>'
            ),
            None,
        ),
        base + "nav_date.do?page=2&iframe=true": (
            200,
            '<a href="/nmos/nmsa-unanno/en/item/18541/index.do">Chapter 41 - Torts</a>',
            None,
        ),
        base + "18541/1/document.do": (200, pdf("41-4-3. Definitions. \n"), None),
    }
    ok = existence(
        pages, {"section": "41-4-3"}, "N.M. Stat. Ann.", tmp_path, monkeypatch
    )
    assert ok.result == "pass" and ok.source == "nmcc-nmonesource"
    no = existence(
        pages, {"section": "52-1-1"}, "N.M. Stat. Ann.", tmp_path / "b", monkeypatch
    )
    assert no.result == "fail" and "no NMSA chapter 52" in no.detail


LA_TOC_URL = "https://www.legis.la.gov/legis/Laws_Toc.aspx?folder=75&level=Parent"
LA_TOC = (
    '<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value="abc" />'
    '<a id="x" href="javascript:__doPostBack(&#39;ctl00$List$ctrl6$LinkButton1a&#39;,'
    '&#39;&#39;)">TITLE 9</a>'
)


def test_louisiana_title_postback_and_section(tmp_path):
    form = vs.la_postback(LA_TOC, "TITLE 9")
    assert b"__EVENTTARGET=ctl00%24List%24ctrl6%24LinkButton1a" in form
    assert vs.la_postback(LA_TOC, "TITLE 99") is None
    pages = {
        LA_TOC_URL: (200, LA_TOC, None),
        (LA_TOC_URL, form): (
            200,
            (
                '<a href="Law.aspx?d=107262">RS 9:2800.54</a>'
                '<a href="Law.aspx?d=1">RS 9:2800.5</a>'
            ),
            None,
        ),
        "https://www.legis.la.gov/legis/Law.aspx?d=107262": (
            200,
            "<span>RS 9:2800.54</span><p>§2800.54. Manufacturer responsibility</p>",
            None,
        ),
    }
    ok = existence(pages, {"section": "9:2800.54"}, "La. Stat. Ann.", tmp_path)
    assert ok.result == "pass"
    no = existence(pages, {"section": "9:2800.99"}, "La. Stat. Ann.", tmp_path / "b")
    assert no.result == "fail"


def test_alabama_graphql(tmp_path):
    def url(sec):
        return (
            "https://alison.legislature.state.al.us/graphql?"
            + vs.urllib.parse.urlencode(
                {"query": vs.ALABAMA_QUERY, "variables": json.dumps({"displayId": sec})}
            )
        )

    hit = {
        "data": {"codesOfAlabama": {"data": [{"displayId": "12-2-7", "title": "S"}]}}
    }
    miss = {"data": {"codesOfAlabama": {"data": []}}}
    pages = {
        url("12-2-7"): (200, json.dumps(hit), None),
        url("12-2-999"): (200, json.dumps(miss), None),
    }
    assert (
        existence(pages, {"section": "12-2-7"}, "Ala. Code", tmp_path).result == "pass"
    )
    assert (
        existence(pages, {"section": "12-2-999"}, "Ala. Code", tmp_path).result
        == "fail"
    )


IND_CONST = (
    "ARTICLE 1.\nBill of Rights\nSection 1. WE DECLARE...\n"
    "   Section 18. The penal code shall be founded...\n"
    "ARTICLE 2.\nSuffrage and Election\nSection 1. All elections shall be free.\n"
)
NM_CONST = (
    "ARTICLE II\nBill of Rights\nSection 1. [Supreme law of the land.]\n"
    "Sec. 10. [Searches and seizures.]\nANNOTATIONS\nSec. 11. of this article\n"
    "ARTICLE III\nSec. 1. [Departments of government.]\n"
)


def test_state_constitutions(tmp_path, monkeypatch):
    ind, _, _, _ = vs.STATE_CONSTITUTIONS["Ind. Const."]
    nm, _, _, _ = vs.STATE_CONSTITUTIONS["N.M. Const."]
    pages = {ind: (200, pdf(IND_CONST), None), nm: (200, pdf(NM_CONST), None)}

    def check(groups, code, d):
        return existence(pages, groups, code, tmp_path / d, monkeypatch).result

    assert check({"article": "1", "section": "18"}, "Ind. Const.", "a") == "pass"
    assert check({"article": "2", "section": "18"}, "Ind. Const.", "b") == "fail"
    assert check({"article": "II", "section": "10"}, "N.M. Const.", "c") == "pass"
    assert check({"article": "II", "section": "1"}, "N.M. Const.", "d") == "pass"
    # an annotation's `Sec. 11.` isn't a section heading
    assert check({"article": "II", "section": "11"}, "N.M. Const.", "e") == "fail"


def test_court_rule_pdfs(tmp_path, monkeypatch):
    trcp, _, _ = vs.COURT_RULES["Tex. R. Civ. P."]
    trap, _, _ = vs.COURT_RULES["Tex. R. App. P."]
    pb, _, _ = vs.COURT_RULES["Conn. Practice Book"]
    pages = {
        trcp: (200, pdf("RULE 185.  SUIT ON ACCOUNT\n"), None),
        trap: (
            200,
            pdf("Rule 25. Perfecting Appeal\n25.2.  Criminal Cases\n2. Item\n"),
            None,
        ),
        pb: (200, pdf("Sec. 63-8. Ordering and Filing of Transcripts\n"), None),
    }

    def check(rule, code, d):
        return existence(pages, {"rule": rule}, code, tmp_path / d, monkeypatch).result

    assert check("185", "Tex. R. Civ. P.", "a") == "pass"
    assert check("186", "Tex. R. Civ. P.", "b") == "fail"
    assert check("25.2", "Tex. R. App. P.", "c") == "pass"
    assert check("25", "Tex. R. App. P.", "d") == "pass"
    assert check("2", "Tex. R. App. P.", "e") == "fail"  # `2. Item` isn't Rule 2
    assert check("63-8", "Conn. Practice Book", "f") == "pass"


def test_refused_sources_stay_with_a_person(tmp_path):
    for code in ("Okla. Stat.", "Ohio Const.", "Mich. Ct. R.", "Pa. R. Civ. P."):
        c = existence({}, {"section": "1", "rule": "1", "article": "I"}, code, tmp_path)
        assert c.result == "none" and "robots.txt" in c.detail


# --- keyed APIs: CourtListener and NY Open Legislation ---------------------------------

CL = vs.COURTLISTENER_API
NY_KEY = "test-ny-key-0123456789"
CL_TOKEN = "test-cl-token-0123456789"


def keyed_pages(court):
    p = pages()
    p.update(
        {
            f"{CL}opinions/1/?fields=cluster": (
                200,
                json.dumps({"cluster": f"{CL}clusters/7/"}),
                None,
            ),
            f"{CL}clusters/7/?fields=docket": (
                200,
                json.dumps({"docket": f"{CL}dockets/9/"}),
                None,
            ),
            f"{CL}dockets/9/?fields=court_id": (
                200,
                json.dumps({"court_id": court["id"]}),
                None,
            ),
            f"{CL}courts/{court['id']}/?fields=id,full_name,jurisdiction": (
                200,
                json.dumps(court),
                None,
            ),
            f"{vs.NY_OPENLEG_API}PEN/70.06?key={NY_KEY}": (
                200,
                json.dumps(
                    {
                        "success": True,
                        "result": {
                            "lawId": "PEN",
                            "locationId": "70.06",
                            "docType": "SECTION",
                            "title": "Sentence of imprisonment for second felony "
                            "offender",
                        },
                    }
                ),
                None,
            ),
            f"{vs.NY_OPENLEG_API}PEN/70.99?key={NY_KEY}": (
                404,
                json.dumps(
                    {
                        "success": False,
                        "message": "The requested law document was not found",
                    }
                ),
                None,
            ),
        }
    )
    return p


def ny_vector(section="70.06"):
    text = f"Penal Law § {section}."
    return vector(
        "ny",
        text,
        [0, len(text) - 1],
        {"reporter": "Penal Law", "section": section, "subject": "Penal"},
        "N.Y. Penal Law",
        "New York",
    )


NY_COURT = {
    "id": "nyappdiv",
    "full_name": "Appellate Division of the Supreme Court of the State of New York",
    "jurisdiction": "SA",
}


def test_keyed_apis_verify_court_and_section(tmp_path, monkeypatch):
    monkeypatch.setenv(vs.COURTLISTENER_TOKEN_ENV, CL_TOKEN)
    monkeypatch.setenv(vs.NY_OPENLEG_KEY_ENV, NY_KEY)
    calls = []
    plain = fake_opener(keyed_pages(NY_COURT))

    def opener(url, follow, headers=None, data=None):
        calls.append((url, headers))
        return plain(url, follow, headers=headers, data=data)

    f = vs.Fetcher(tmp_path / "cache", {}, opener=opener)
    vectors = [ny_vector(), {**ny_vector("70.99"), "id": "t/find/ny_missing"}]
    results = {
        r["id"].split("/")[-1]: r for r in vs.run([write_set(tmp_path, vectors)], f)
    }
    assert results["ny"]["verdict"] == (
        f"verified-by-source:courtlistener-api+ny-openleg+reporters-db@"
        f"{vs.REPORTERS_DB_TAG}"
    )
    assert results["ny_missing"]["verdict"].startswith(
        "contradicted:existence: " + vs.NY_OPENLEG_API + "PEN/70.99: HTTP 404"
    )
    # The token goes in a header and the key in the query string of the request only.
    assert all(h == {"Authorization": f"Token {CL_TOKEN}"} for u, h in calls if CL in u)
    # Neither the lock, the cache, the verdicts nor the report holds either secret.
    md = vs.markdown(list(results.values()), f.used)
    written = [json.dumps(f.used), json.dumps(list(results.values())), md]
    written += [p.read_bytes().decode(errors="replace") for p in f.cache.iterdir()]
    for blob in written:
        assert NY_KEY not in blob and CL_TOKEN not in blob
    assert f"{vs.NY_OPENLEG_API}PEN/70.06" in f.used


def test_citing_court_elsewhere_stays_with_a_person(tmp_path, monkeypatch):
    monkeypatch.setenv(vs.COURTLISTENER_TOKEN_ENV, CL_TOKEN)
    court = {"id": "ca8", "full_name": "Court of Appeals for the Eighth Circuit"}
    f = vs.Fetcher(
        tmp_path / "cache",
        {},
        opener=fake_opener(keyed_pages({**court, "jurisdiction": "F"})),
    )
    (r,) = vs.run([write_set(tmp_path, [ny_vector()])], f)
    form = [c for c in r["checks"] if c["claim"] == "form"]
    assert [c["result"] for c in form] == ["none"]
    assert (
        "cited by Court of Appeals for the Eighth Circuit (`ca8`)"
        in (form[0]["detail"])
    )
    # The NY key is unset here: the section check is recorded as not run.
    ex = next(c for c in r["checks"] if c["claim"] == "existence")
    assert ex["result"] == "not-run" and vs.NY_OPENLEG_KEY_ENV in ex["detail"]


def test_without_keys_the_checks_are_not_run(tmp_path):
    opener = fake_opener(keyed_pages(NY_COURT))
    f = vs.Fetcher(tmp_path / "cache", {}, opener=opener)
    (r,) = vs.run([write_set(tmp_path, [ny_vector()])], f)
    assert r["verdict"] == "unverifiable:existence, form"
    assert not [u for u in opener.calls if CL in u or vs.NY_OPENLEG_API in u]
    not_run = [c["detail"] for c in r["checks"] if c["result"] == "not-run"]
    assert len(not_run) == 2
    md = vs.markdown([r], f.used)
    assert "## Checks not run" in md
    assert f"citing court not checked: {vs.COURTLISTENER_TOKEN_ENV} is unset: 1" in md


def test_court_jurisdiction():
    def j(name, kind="S"):
        return vs.cl_court_jurisdiction({"full_name": name, "jurisdiction": kind})

    assert j("Supreme Court of West Virginia") == "West Virginia"
    assert j("Supreme Court of Virginia") == "Virginia"
    assert j("Court of Appeals of Arkansas", "SA") == "Arkansas"
    assert j("District Court, N.D. Georgia", "FD") == "United States"
    assert j("Court of Appeals for the Armed Forces", "MA") is None


def test_rate_limit_backs_off_and_retries(tmp_path, monkeypatch):
    waits = []
    monkeypatch.setattr(vs.time, "sleep", waits.append)
    answers = [(429, b"", None), (429, b"", None), (200, b"ok", None)]

    def opener(url, follow):
        return answers.pop(0)

    f = vs.Fetcher(tmp_path, {}, opener=opener)
    assert f.get("https://x/limited") == (200, b"ok")
    assert waits == [15, 30]
    assert vs._retry_after({}, b"Expected available in 49 seconds.") == 49
    assert vs._retry_after({"Retry-After": "7"}, b"") == 7

    def always(url, follow):
        return 429, b"", None

    with pytest.raises(vs.SourceUnavailable, match="429"):
        vs.Fetcher(tmp_path / "b", {}, opener=always).get("https://x/never")


def test_secret_query_stays_out_of_errors(tmp_path):
    def down(url, follow):
        raise vs.SourceUnavailable(f"{url}: connection refused")

    f = vs.Fetcher(tmp_path, {}, opener=down)
    with pytest.raises(vs.SourceUnavailable) as e:
        f.get("https://x/api", query={"key": NY_KEY})
    assert NY_KEY not in str(e.value) and e.value.__cause__ is None


def test_a_long_rate_limit_wait_ends_the_host_for_the_run(tmp_path, monkeypatch):
    monkeypatch.setattr(vs.time, "sleep", lambda s: pytest.fail("waited"))
    calls = []

    def quota(*args, **kwargs):
        calls.append(args[0])
        raise vs.RateLimited(args[0], 1377)

    monkeypatch.setattr(vs, "_urlopen", quota)
    f = vs.Fetcher(tmp_path, {})
    with pytest.raises(vs.RateLimitExhausted):
        f.get("https://cl.example/a")
    with pytest.raises(vs.RateLimitExhausted):
        f.get("https://cl.example/b")
    assert f.exhausted == {"cl.example"}
    assert calls == ["https://cl.example/a"]  # /b never went out


def test_server_errors_are_not_cached(tmp_path):
    answers = [(502, b"bad gateway", None), (200, b"ok", None)]
    f = vs.Fetcher(tmp_path, {}, opener=lambda url, follow: answers.pop(0))
    assert f.get("https://x/flaky") == (502, b"bad gateway")
    assert "https://x/flaky" not in f.used
    assert f.get("https://x/flaky") == (200, b"ok")
