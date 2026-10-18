# Documentation

This documentation is maintained on `main`. Start with the repository
[README](../README.md) for installation and a quick example; the guides below
cover use, compatibility and maintenance.

## Start here

| Document | Purpose |
| --- | --- |
| [README](../README.md) | Installation, quick start and examples |
| [Supported versions](supported-versions.md) | Tested ABACUS snapshots, readers and limitations |
| [Troubleshooting](troubleshooting.md) | Common setup, asset and runtime problems |

## User guides

| Document | Purpose |
| --- | --- |
| [Usage](usage.md) | Calculator configuration, examples and output reading |
| [Migration](migration.md) | Installing the independent package and adapting callers |
| [Compatibility and CI](compatibility-ci.md) | Current checks, evidence and remaining gaps |
| [Changelog](../CHANGELOG.md) | User-visible changes and release history |

## Development

| Document | Purpose |
| --- | --- |
| [Contributing](../CONTRIBUTING.md) | Development setup, tests, packaging and review |
| [Design](design.md) | Package responsibilities and architectural constraints |
| [From ase-abacus to abacuslite](ase-interface.md) | Differences from the old ASE fork and the current architecture |
| [Module reference](reference.md) | Public API and output-format details |
| [Source provenance](../UPSTREAM.md) | Original authorship, imported revisions and adaptations |
| [Upstream integration audit](upstream-integration.md) | Source comparison and reader-isolation rationale |
| [Internal conventions](../AGENTS.md) | Repository-specific automation and agent conventions |

## Maintainer records

Dated plans and evidence describe what was tested at a particular revision.
They are historical records; use the guides above for current behavior.

- [Post-release ATST and engine integration](superpowers/plans/2026-10-18-atst-next-actions.md):
  external-only consumers, dual-engine builds and hosted checks.
- [1.1.0 release](superpowers/plans/2026-10-17-1.1.0-release.md):
  release artifacts and publication evidence.
- [Dual-engine CI follow-up](superpowers/plans/2026-10-17-dual-engine-ci.md):
  portable harness and engine-side implementation record.
- [ABACUS/ATST integration acceptance](superpowers/plans/2026-10-17-abacus-atst-integration-acceptance.md):
  local acceptance evidence and tested revision tuples.
- [Standalone bootstrap](superpowers/plans/2026-10-16-standalone-bootstrap.md):
  original extraction and package-validation record.
- [Cross-repository regressions](superpowers/plans/2026-10-16-cross-repository-regressions.md):
  initial installed-consumer tests and source-integration evidence.
