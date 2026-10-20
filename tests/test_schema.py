"""Every committed vector has to match schema/vector.schema.json."""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = {p.name: json.loads(p.read_text()) for p in (ROOT / "schema").glob("*.json")}
REGISTRY = Registry().with_resources(
    (s["$id"], Resource.from_contents(s)) for s in SCHEMAS.values()
)
VECTOR = Draft202012Validator(SCHEMAS["vector.schema.json"], registry=REGISTRY)
FILES = sorted((ROOT / "vectors").glob("*/*.jsonl"))


def test_schemas_are_valid():
    for schema in SCHEMAS.values():
        Draft202012Validator.check_schema(schema)


@pytest.mark.parametrize("path", FILES, ids=lambda p: str(p.relative_to(ROOT)))
def test_vectors_match_the_schema(path):
    errors = [
        f"{v['id']} {'/'.join(map(str, e.absolute_path))}: {e.message}"
        for v in map(json.loads, path.read_text().splitlines())
        for e in VECTOR.iter_errors(v)
    ]
    assert not errors, "\n".join(errors)


def test_an_integer_opinion_fails():
    # #29: three CAP vectors once had "opinion": 0, an index, where the schema wants a string.
    lines = (ROOT / "vectors/statutes/find.jsonl").read_text().splitlines()
    v = next(v for v in map(json.loads, lines) if v["id"] == "statutes/find/pa_ps/1")
    assert not list(VECTOR.iter_errors(v))
    v["source"]["opinion"] = 0
    assert [e.json_path for e in VECTOR.iter_errors(v)] == ["$.source.opinion"]
