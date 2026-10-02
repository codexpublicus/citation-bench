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
        out["full_span"] = list(cite.full_span())
    if isinstance(cite, ResourceCitation):
        out["reporter_normalized"] = cite.corrected_reporter()
        out["year"] = cite.year
    return out


def resolution(cites, resolutions):
    """For each citation in document order, the index of its resource group or None.

    Groups are numbered by the position of their first citation, so the labels don't
    depend on how an engine orders its resources.
    """
    group_of = {
        id(c): g for g, members in enumerate(resolutions.values()) for c in members
    }
    seen = {}
    return [
        None if id(c) not in group_of else seen.setdefault(group_of[id(c)], len(seen))
        for c in cites
    ]
