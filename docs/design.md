# Package design

abacuslite owns the installable ASE calculator and the ABACUS input/output
readers. It depends on ASE and supports the tested develop and LTS output
formats. Output parsing is read-only and repeatable; each calculator keeps its
reader selection. See the [public API](public-api.md) for caller-visible
behavior and [supported versions](supported-versions.md) for tested snapshots.

## Responsibilities

- ASE owns calculator contracts and optimization, MD and NEB algorithms.
- ABACUS owns the engine, input/output formats, assets and engine integration tests.
- This package owns the ASE calculator and general input/output parsing.
- ATST and Forge own their workflow, launcher and result-projection policies;
  they are consumers, not runtime dependencies.

General parser or calculator fixes belong here. Engine format changes belong
in ABACUS and should be checked against this package. Cross-repository changes
use linked candidate revisions and the checks in [compatibility and CI](compatibility-ci.md).

ABACUS PR [#8175](https://github.com/deepmodeling/abacus-develop/pull/8175)
proposes installing this package in the engine repository. It remains open, so
current ownership and the bundled source remain unchanged until upstream
maintainers decide otherwise. The package and its tests continue to be
maintained here.

## Tests and fixtures

Tests should establish a specific public behavior or protect a parser rule that
would otherwise be difficult to reproduce. Prefer existing integration or
synthetic fixtures when they cover the same format and failure. Add a recorded
output fixture only when a real formatting or unit detail matters; keep the
smallest input that reproduces that behavior and identify its source. Do not
copy tests to reproduce the same assertion at multiple layers unless each layer
protects a distinct contract.

Offline package tests validate the installed parser and calculator without an
engine. Opt-in engine tests validate real calculator interaction with a named
engine and assets. Installed-consumer checks validate the public package
boundary. The separate checks answer different questions; one does not replace
the others. Published wheel and sdist artifacts contain runtime code and
necessary package metadata, not tests, recorded logs, examples or development
history. See [Contributing](../CONTRIBUTING.md) for artifact verification.

## Assets and provenance

Profiles accept explicit pseudopotential and orbital directories. When an
argument is omitted, only ABACUS_PP_PATH and ABACUS_ORB_PATH provide package
defaults. Dataset downloads, element matching and asset preparation belong to
abacustest or abacusforge. Original authorship and imported source revisions
are recorded in [UPSTREAM.md](../UPSTREAM.md).
