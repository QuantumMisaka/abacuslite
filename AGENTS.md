# abacuslite development

## Goal and scope

Maintain one independently installable ABACUS calculator and I/O plugin for ASE.
Preserve public `abacuslite` imports, upstream attribution and read-only parsing
while consolidating general-purpose fixes from ABACUS and ATST. Pure file I/O
must work without an ABACUS executable.

## Upstream and downstream boundaries

- ASE supplies calculator contracts and optimization/MD/NEB algorithms.
- ABACUS owns the engine, output formats, assets and engine integration tests.
  Support develop's newer format and LTS through `legacyio`; bind reader
  selection to each calculator instance, even when LTS has no bundled interface.
- ATST consumes calculator/I/O behavior and owns workflow and launcher policy.
- Forge consumes the optional parser and owns its native default and result
  contracts. ATST and Forge are not runtime dependencies of this package.
- Keep general parser/calculator fixes here. Compatibility adapters may forward
  to this implementation; do not add duplicate parsers, schedulers, workflow
  orchestration or consumer result schemas to the package.

## Development workflow

1. Read [the documentation index](docs/README.md), [design](docs/design.md),
   [module reference](docs/reference.md) and [source provenance](UPSTREAM.md)
   for the affected area. Reuse an applicable plan for coordinated work.
2. Make focused, reversible changes within the agreed design. Update the
   relevant design/plan before changing public or cross-repository boundaries;
   continue within approved scope without reopening routine implementation choices.
3. Add regressions for observable behavior changes. For behavior-preserving
   extraction or packaging changes, compare baseline and candidate behavior.
   Preserve units, atom order and missing-value meaning. Parsing existing
   output must not modify or delete input/output files.
4. Follow [CONTRIBUTING.md](CONTRIBUTING.md) for commands. Default tests are
   offline; real-engine and installed-consumer checks require explicit opt-in
   and supplied dependencies/assets. Validate built wheels outside the source
   checkout; source-only success is not release evidence.
5. Test affected develop/LTS and consumer boundaries using the
   [compatibility guide](docs/compatibility-ci.md). Fixture success does not
   establish engine compatibility; report local results, remote CI and merge
   enforcement separately. Validate locally before PR delivery.
6. Use English for documentation and new diagnostics/docstrings, retain source
   attribution, and record material compatibility changes in `CHANGELOG.md`.
   Obtain independent review before integration. PyPI publication requires
   validated artifacts and explicit release authorization.

Current guidance lives in the root entry documents and `docs/`. Implementation
plans and dated evidence live in `docs/superpowers/plans/`; historical results
apply only to their recorded revisions and environments.
