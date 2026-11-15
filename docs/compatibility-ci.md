# Compatibility and CI

The published [1.2.2 package](https://pypi.org/project/abacuslite/1.2.2/)
supports the tested develop and LTS ABACUS output formats. This does not certify
every engine revision or imply that the independent package has been adopted
upstream. [ABACUS PR #8175](https://github.com/deepmodeling/abacus-develop/pull/8175)
remains open; the bundled source is still maintained in the ABACUS repository.

## What CI checks

The Package tests workflow runs on pushes, pull requests, merge queues, manual
runs and a weekly schedule.

- **Installed package:** builds and checks wheel and source distributions,
  installs each runtime artifact, and runs offline tests outside the checkout
  on Python 3.10 with minimum dependencies and Python 3.12 with current
  dependencies. The sdist-derived wheel is tested with test assets from the
  same source revision. Tests, examples, recorded output and development
  documents are excluded from both distributions.
- **Installed consumers:** installs selected ATST and Forge revisions alongside
  the candidate wheel and verifies the consumer suite and this package's
  integration contracts. Consumer packages remain outside runtime dependencies.
- **Engine compatibility:** resolves one set of ABACUS, harness and asset
  revisions, cold-builds develop and LTS, installs the candidate package and
  runs required cases through public interfaces.
- **Aggregate gate:** fails if a required package, consumer, reference or engine
  job fails or is skipped.

Pull request runs use pinned consumer revisions; scheduled runs follow their
main branches. Manual runs accept candidate refs for coordinated changes.
Every compatibility result should identify the plugin, engine, harness and
asset revisions. Reports and raw engine outputs are retained by CI, including
failed engine jobs.

## Supported behavior and limits

Each calculator selects its reader from its configured executable and keeps
that choice for its lifetime. The tested develop 3.11 output uses latestio;
ABACUS 3.10.x LTS uses legacyio. See [Supported versions](supported-versions.md)
for exact snapshots and known limits.

Engine-side integration tests belong to ABACUS and compare parser results with
raw engine outputs. Package offline tests cover parser and public ASE behavior
without launching ABACUS. Consumer tests check installed-package boundaries.
These checks protect different behaviors; fixture tests do not certify engine
execution, and one repository's parser must not be used as the oracle for
another repository's parser.

LTS has no socket driver in the tested v3.10.1 build. The fixed-cell socket
calculator therefore requires an engine build with socket support. Short
integration cases test interface behavior and do not establish scientific
convergence or equivalence between engine versions.

## Changing a boundary

For parser changes, keep a small attributed regression in this package and
reuse an existing output fixture when it covers the same behavior. ABACUS tests
engine behavior through its existing engine harness and raw-property
assertions; do not copy this package's tests or fixture logs into the ABACUS
repository. When useful, the standalone suite can be run against the bundled
source from outside the ABACUS checkout. For consumer changes, test installed
wheels against explicit candidate refs. Do not submit hosted HPC runs from
ordinary community pull requests; trusted maintainers run the engine workflow.

Keep the external ABACUS and consumer PRs linked while behavior changes cross
repository boundaries. Upstream ABACUS branch protection is not visible from
this repository, so this guide makes no claim about its required checks.
The GitHub Actions workflow and [Contributing](../CONTRIBUTING.md) are the
current sources for CI and local verification details.
