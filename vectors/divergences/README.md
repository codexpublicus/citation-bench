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
| `id-section-pin` | `find` and `resolve`, 34 inputs each | `Id. § 5` keeps `§ 5` as its pin cite, including the longer forms from citare#48 (`, subd. (a)`, `, cmt. (n.2)`, `[4]`, ` to 216.111`, a line break or NBSP after the `§`, U+2010 hyphens). eyecite gives a bare `Id.` and a separate unknown citation for the `§`. After a case, the section pin cite leaves the id. citation unresolved, by the rule eyecite already applies to `Id. ¶ 4`. After a statute or a paged law citation (`83 Stat. 841`), it resolves, and an id. citation after it keeps resolving where eyecite's unknown `§` breaks the chain. |
| `law-section` | `find`, 5 inputs | A statute section number may end in a letter (`Mich. Comp. Laws § 600.2912a`, `42 U.S.C. § 2000e-5`), have letters after a hyphen (`§ 394-ccc`) and use U+2010 or U+2011 as a hyphen (citare#48). eyecite cuts each at the first part (`§ 600`) or, for `§ 2000e-5`, finds no law citation. |
| `supra-after-parallel` | `resolve`, 4 inputs | A supra whose case name matches a decision cited in parallel (`Smith v. Jones, 275 Conn. 38, 881 A.2d 194`; `410 U.S. 113, 93 S. Ct. 705, 35 L. Ed. 2d 147`) resolves to the first of its citations, and an id. citation after it follows (citare#60). eyecite finds two or three resources and leaves the supra unresolved. Includes the Connecticut habit of repeating the regional cite after each supra, and a decision cited alone before it is cited in parallel. |

Adding a divergence: write it up in citare's `docs/divergences.md` first, then add `find`
and, if resolution changes, `resolve` vectors here with ids `divergences/<kind>/<case>/<n>`,
check each expected citation by hand, and run
`mise run bench:divergences eyecite -- --update-known-failures` to add the new ones eyecite
misses to its baseline.
