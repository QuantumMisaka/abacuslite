# abacuslite development

abacuslite is an independent ABACUS calculator and I/O plugin for ASE.
Read `UPSTREAM.md`, `docs/design.md`, and the active plan before implementation.

- Preserve public `abacuslite` imports and original source attribution.
- Keep workflow orchestration, schedulers, and consumer result schemas outside
  this package. Pure I/O must not require an ABACUS executable.
- Parsing existing output must not delete or modify input artifacts.
- Validate behavior changes with focused regressions; use baseline/candidate
  evidence for source extraction and packaging changes.
- Default tests are offline. Real engine tests require `--run-engine` and
  caller-provided executables and assets.
- Test built wheels outside the source checkout. Source-only success is not
  release evidence. Do not claim engine compatibility from fixture tests.
- New diagnostics and docstrings use English; preserve attribution in imported
  code. Document material compatibility changes in `CHANGELOG.md`.
- Use an independent reviewer before integration. Publishing to PyPI follows
  validated release artifacts and explicit release authorization.
