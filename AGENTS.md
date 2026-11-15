# abacuslite development

Maintain one independently installable ABACUS calculator and I/O plugin for
ASE. Preserve public imports, source attribution and read-only parsing; pure
file I/O must work without an ABACUS executable.

## Boundaries

- ASE owns calculator contracts and optimization/MD/NEB algorithms.
- ABACUS owns the engine, output formats, assets and engine-side tests. Support
  develop and LTS readers, bound to each calculator. ABACUS PR #8175 proposes
  installing this package and keeping the engine-side harness under
  `interfaces/ASE_interface`; adoption remains pending upstream review. This
  repository continues to own the calculator, parser and package tests.
- ATST and Forge consume this package and own workflow, launcher and result
  contracts. Neither is a runtime dependency.
- Keep general parser/calculator fixes here. Adapters may forward, but do not
  add duplicate parsers, schedulers, orchestration or consumer result schemas.
- Asset provisioning, dataset downloads, element matching and batch
  preparation belong to abacustest/abacusforge. The only environment fallbacks
  in this package are `ABACUS_PP_PATH` and `ABACUS_ORB_PATH` for directory
  defaults.

## Invariants

- Preserve public imports, units, atom order, missing values and read-only
  parsing.
- Add regressions for behavior changes; compare baseline and candidate for
  packaging or extraction changes.
- Never weaken assertions or tolerances to make a test pass.
- Use English for docs and new diagnostics; retain attribution and record
  material compatibility changes in `CHANGELOG.md`.

## Workflow

1. Read `docs/README.md` and the guide for the affected area. Reuse and update
   a relevant plan in the maintainer workspace before changing a public or
   cross-repository boundary.
2. Follow [CONTRIBUTING.md](CONTRIBUTING.md) for setup, tests, packaging and
   release. Default tests are offline; engine and consumer checks need
   explicit assets.
3. Validate built wheels outside the checkout. Source-only or fixture-only
   success is not engine or release evidence; report local, hosted CI and
   enforcement results separately.
4. Obtain independent review before integration. Never move a published tag
   or replace a published artifact; PyPI publication needs validated
   artifacts and explicit authorization.

Development plans and detailed run evidence live in the maintainer workspace,
outside the source distribution. For current behavior, use the guides and
`CHANGELOG.md`.
