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
`tests/integration/` is marked `engine`, and `tests/consumers/` is marked
`consumer`. Tests elsewhere must use `@pytest.mark.engine` or
`@pytest.mark.consumer` when they need those resources; function names and
checkout directory names do not select a test tier. Unknown markers and
pytest configuration keys fail validation. `-m engine` selects tests but does
not enable execution without `--run-engine`.

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
Use the tests, examples and configuration extracted from that sdist for the
second run, so missing distribution files cannot be masked by the checkout.
CI uses this layout for Python 3.10 with the declared direct dependency floors
and Python 3.12 with current dependencies. Tests and examples ship in the
sdist; the wheel contains the runtime package only.
Use `python -I -m pytest -q` for artifact validation: example subprocesses
preserve isolated mode and check that a conflicting `PYTHONPATH` is ignored.

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
for installed ATST/Forge checks, the portable harness and current develop/LTS
evidence. The package workflow cold-builds both engines using
`scripts/ci/build_abacus.sh`; reviewed sources and asset hashes are in
`tests/engine-refs.json`. Changes to CI helpers should run
`python -m pytest .github/tests -q` as well as workflow validation.
Fixture or example-startup success alone is not real-engine acceptance.

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

## Cross-repository changes

Shared contracts include the ASE calculator API, ABACUS output formats and the
socket protocol ([adapter contract](docs/socket-contract.md)). For a change
that crosses repositories:

1. Agree on the compatibility and version rule first; additive changes and
   breaking changes need different rollout paths.
2. Open linked PRs in this repository and in the owning upstream.
3. Run engine-side and installed-adapter checks against the candidate pair.
4. Update [supported versions](docs/supported-versions.md) and the
   [compatibility record](docs/compatibility-ci.md).

Do not land a breaking wire-format change on one side only.

## Releasing

Stable releases require explicit maintainer authorization, reviewed changes,
installed-wheel/sdist checks and successful `Package tests` for the release
tag. Preserve affected develop/LTS and consumer evidence. Set the version in
`pyproject.toml`, update the changelog, and merge the reviewed source into main
before creating its `vMAJOR.MINOR.PATCH` tag. Never move a published tag or
replace a published distribution.

The manual `Publish to PyPI` workflow must run from main. Supply the stable tag
and the successful **tag push** run ID of `Package tests`. It checks the source
repository, workflow, event, revision, main ancestry and artifact versions,
then publishes that run's `distributions-3.12` artifact without rebuilding.
Only the upload job receives OIDC permission. The `pypi` GitHub environment
must match a PyPI Trusted Publisher for owner `QuantumMisaka`, repository
`abacuslite`, workflow `publish.yml`, environment `pypi`. A first release uses
a pending publisher configured by the maintainer in their PyPI account.

After upload, compare PyPI's SHA256 digests with the workflow summary and
verify `pip install abacuslite==VERSION` and `pip check` in a fresh environment.
If an upload partially succeeds, inspect the registry before retrying; do not
silently skip conflicting artifacts. Keep the release's source/run IDs and
verification evidence in its record under `docs/superpowers/plans/`.
