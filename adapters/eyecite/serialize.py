"""Convert eyecite citation objects to the bench's engine-neutral form (docs/protocol.md)."""

from eyecite.models import ResourceCitation

TYPES = {
    "FullCaseCitation": "full_case",
    "ShortCaseCitation": "short_case",
    "SupraCitation": "supra",
    "IdCitation": "id",
    "ReferenceCitation": "reference",
    "FullLawCitation": "full_law",
    "FullJournalCitation": "full_journal",
    "UnknownCitation": "unknown",
}

# Positional bookkeeping, not part of what a citation says.
_SKIP_METADATA = {"pin_cite_span_start", "pin_cite_span_end"}


def citation(cite, with_span=True):
    out = {
        "type": TYPES[type(cite).__name__],
        "groups": {k: v for k, v in cite.groups.items() if v is not None},
        "metadata": {
            k: str(v)
            for k, v in vars(cite.metadata).items()
            if v is not None and k not in _SKIP_METADATA
        },
    }
    if with_span:
        out["span"] = list(cite.span())
    if isinstance(cite, ResourceCitation):
        out["reporter_normalized"] = cite.corrected_reporter()
        out["year"] = cite.year
    return out
