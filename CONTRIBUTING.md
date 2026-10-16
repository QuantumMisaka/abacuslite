# Contributing

General ASE calculator and ABACUS I/O fixes belong in this package. ABACUS
owns the engine and its integration harness; ATST owns workflow and launcher
policy. See the [integration audit](docs/upstream-integration.md) and
[cross-repository CI guide](docs/compatibility-ci.md) before changing a boundary.

Use the development commands in README.md. Add a regression for the observable
bug, with a small attributed fixture when output formats matter. Preserve units,
atom ordering, missing-value meaning, readonly parsing and public imports.
Validate the built wheel, not only editable source. For a parser or calculator
change, identify affected supported engine versions and consumers and collect
real-engine evidence where needed before release.

CI and fixtures are part of the contract: explain changed expectations and
link paired repository PRs. Internal refactoring is welcome when the behavior
continues to pass. Breaking public behavior needs an explicit migration and
versioning decision; do not silently weaken existing assertions.
