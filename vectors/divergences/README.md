# Divergence vectors

These vectors encode outputs that **deliberately differ from eyecite**. Each one is an input
where citare gives a different answer from eyecite 2.7.8 on purpose, and the expected output
is citare's. They are scored separately from `vectors/eyecite-*`, so eyecite still scores
100% on its own tests:

```bash
mise run bench:divergences eyecite   # fails only on vectors not in baselines/eyecite.known-differences
mise run bench:divergences citare    # fails only on vectors not in baselines/citare.known-failures
```

`baselines/eyecite.known-differences` lists every vector here that eyecite gets "wrong". It is
not a to-do list for eyecite: an entry leaves it when eyecite adopts the behavior, or when the
divergence is withdrawn. Until citation-bench's locked citare commit includes a divergence,
its vectors are also in `baselines/citare.known-failures`.

Each divergence is written up in citare's
[`docs/divergences.md`](https://github.com/codexpublicus/citare/blob/main/docs/divergences.md):
the example input, both engines' output, the evidence from real opinions that citare's answer
is the better one, and the eyecite issue that reports it. A vector's `source.test` names its
entry there (`id-section-pin/<case>`), and `source.note` says what the case exercises.

| Entry | Vectors | What differs |
|---|---|---|
| `id-section-pin` | `find` and `resolve`, 18 inputs each | `Id. § 5` keeps `§ 5` as its pin cite. eyecite gives a bare `Id.` and a separate unknown citation for the `§`. After a case, the section pin cite leaves the id. citation unresolved, by the rule eyecite already applies to `Id. ¶ 4`. After a statute or a paged law citation (`83 Stat. 841`), it resolves, and an id. citation after it keeps resolving where eyecite's unknown `§` breaks the chain. |

Adding a divergence: write it up in citare's `docs/divergences.md` first, then add `find`
and, if resolution changes, `resolve` vectors here with ids `divergences/<kind>/<case>/<n>`,
check each expected citation by hand, and run
`mise run bench:divergences eyecite -- --update-known-failures` to add the new ones eyecite
misses to its baseline.
