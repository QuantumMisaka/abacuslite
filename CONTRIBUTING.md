# Contributing

General ASE calculator and ABACUS I/O fixes belong in this package. ABACUS
owns the engine and its integration harness; ATST owns workflow and launcher
policy. See the [integration audit](docs/upstream-integration.md) and
[cross-repository CI guide](docs/compatibility-ci.md) before changing a boundary.

## Development setup

From the repository root in a suitable Python environment:

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
```

The default suite is offline; engine and external-consumer tests are opt-in.
Editable installs are appropriate for development. For acceptance, build wheel
and sdist distributions and check their metadata:

```bash
python -m build
python -m twine check --strict dist/*
```

Install the built wheel and pytest in a fresh environment, run `pip check`,
and copy `tests/`, `examples/` and `pyproject.toml` to a directory outside the
source checkout. Run `python -m pytest -q` there without a source `PYTHONPATH`.
Verify that `abacuslite.__file__` resolves inside that environment; the
[migration guide](docs/migration.md#install-one-implementation) provides the
check. Include `examples/` because offline tests verify their startup. Repeat
with a wheel rebuilt from the sdist when validating distribution changes.

## Engine and consumer checks

For the package's opt-in engine tests, supply the matching ABACUS build and
the tests' named pseudopotential/orbital assets:

```bash
export ABACUS_COMMAND='mpirun -np 2 abacus'
export ABACUS_PP_ORB=/absolute/path/to/ABACUS/tests/PP_ORB
export OMP_NUM_THREADS=1
python -m pytest --run-engine -m engine -q
```

These imported tests contain engine-specific references and do not replace the
stronger two-format engine harness. Consult the [compatibility guide](docs/compatibility-ci.md)
for installed ATST/Forge checks, current develop/LTS evidence and pending CI
work. Fixture or example-startup success alone is not real-engine acceptance.

## Changes and review

Add a regression for the observable bug, with a small attributed fixture when
output formats matter. Preserve units,
atom ordering, missing-value meaning, readonly parsing and public imports.
Validate the built wheel, not only editable source. For a parser or calculator
change, identify affected supported engine versions and consumers and collect
real-engine evidence where needed before release.

CI and fixtures are part of the contract: explain changed expectations and
link paired repository PRs. Internal refactoring is welcome when the behavior
continues to pass. Breaking public behavior needs an explicit migration and
versioning decision; do not silently weaken existing assertions.

Historical implementation evidence is retained in the
[bootstrap record](docs/superpowers/plans/2026-10-16-standalone-bootstrap.md)
and [installed-consumer CI record](docs/superpowers/plans/2026-10-16-cross-repository-regressions.md).
Current engine/consumer results and subsequent plans are linked from the
compatibility guide.
