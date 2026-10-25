"""data/law-codes.json covers every code the vectors name, each with its Bluebook form."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODES = json.loads((ROOT / "data" / "law-codes.json").read_text())["codes"]


def vector_codes():
    """{reporter_normalized: [vector id, ...]} over every vector set."""
    out = {}
    for path in sorted((ROOT / "vectors").glob("*/*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            v = json.loads(line)
            for c in (v.get("expected") or {}).get("citations") or []:
                if c.get("type") == "full_law" and c.get("reporter_normalized"):
                    out.setdefault(c["reporter_normalized"], []).append(v["id"])
    return out


def test_every_code_in_the_vectors_has_an_entry_with_a_bluebook_alias():
    used = vector_codes()
    assert used, "no full_law citations found under vectors/"
    missing = {code: ids[:3] for code, ids in used.items() if code not in CODES}
    assert not missing, f"codes with no entry in data/law-codes.json: {missing}"
    for code in used:
        kinds = [a["kind"] for a in CODES[code]["aliases"]]
        assert "bluebook" in kinds, f"{code} has no Bluebook alias"


def test_entries_are_complete():
    for code, e in CODES.items():
        assert e["jurisdiction"] and e["name"] and e["basis"], code
        for a in e["aliases"]:
            assert a["kind"] in ("bluebook", "reporters-db"), (code, a)
            assert a["form"] and a["source"], (code, a)
            if a["kind"] == "bluebook":
                # Where a Bluebook form comes from: memory, or a source named for it.
                assert a["source"] == "memory" or a["source"].startswith("http"), code
        # reporters-db's key is an alias wherever the identifier differs from it.
        rdb = e["reporters_db"]
        if rdb and rdb != code:
            forms = [a["form"] for a in e["aliases"] if a["kind"] == "reporters-db"]
            assert forms == [rdb], code
