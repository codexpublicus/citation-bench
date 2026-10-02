"""Scorer tests on tiny synthetic vectors."""

from run import canonical_resolution, compare


def cite(type_="full_case", **kw):
    c = {
        "type": type_,
        "groups": {"volume": "1", "reporter": "U.S.", "page": "1"},
        "metadata": {},
    }
    c.update(kw)
    return c


def vector(kind="find", fmt="plain", **expected):
    return {
        "id": "t/0",
        "kind": kind,
        "input": {"text": "1 U.S. 1", "format": fmt},
        "expected": expected,
    }


def test_find_pass_and_missing_response():
    v = vector(citations=[cite()])
    assert compare(v, {"citations": [cite()]}) == []
    assert compare(v, None) == ["no-response"]
    assert compare(v, {"error": "boom"}) == ["error"]


def test_find_type_mismatch_is_citations():
    v = vector(citations=[cite()])
    assert compare(v, {"citations": [cite("short_case")]}) == ["citations"]
    assert compare(v, {"citations": []}) == ["citations"]


def test_find_field_mismatches():
    v = vector(
        citations=[
            cite(span=[0, 8], reporter_normalized="U.S.", metadata={"court": "scotus"})
        ]
    )
    got = cite(span=[0, 7], reporter_normalized="U. S.", metadata={"court": "x"})
    got["groups"] = {"volume": "2", "reporter": "U.S.", "page": "1"}
    assert compare(v, {"citations": [got]}) == [
        "groups",
        "metadata.court",
        "reporter_normalized",
        "span",
    ]


def test_spans_only_scored_when_expected_and_plain():
    no_span = vector(citations=[cite()])
    assert compare(no_span, {"citations": [cite(span=[3, 4])]}) == []
    html = vector(fmt="html", citations=[cite(span=[0, 8], full_span=[0, 8])])
    assert compare(html, {"citations": [cite(span=[9, 9], full_span=[1, 2])]}) == []
    plain = vector(citations=[cite(full_span=[0, 8])])
    assert compare(plain, {"citations": [cite(full_span=[0, 9])]}) == ["full_span"]


def test_unscored_metadata_is_ignored():
    v = vector(citations=[cite()])
    assert compare(v, {"citations": [cite(metadata={"resolved_case_name": "X"})]}) == []


def test_canonical_resolution():
    assert canonical_resolution([3, 3, None, 1, 3]) == [0, 0, None, 1, 0]
    assert canonical_resolution(None) == []


def test_resolve_compares_partitions():
    cites = [cite(), cite("id", groups={})]
    v = vector("resolve", citations=cites, resolution=[0, 0])
    assert compare(v, {"citations": cites, "resolution": [7, 7]}) == []
    assert compare(v, {"citations": cites, "resolution": [0, None]}) == ["resolution"]
    assert compare(v, {"citations": cites}) == ["resolution"]
    assert compare(v, {"citations": cites[:1], "resolution": [0]}) == ["citations"]


def test_annotate_compares_text():
    v = vector("annotate", text="<0>1 U.S. 1</0>")
    assert compare(v, {"text": "<0>1 U.S. 1</0>"}) == []
    assert compare(v, {"text": "1 U.S. 1"}) == ["text"]


def test_unknown_kind():
    assert compare(vector("frobnicate"), {}) == ["unknown-kind:frobnicate"]
