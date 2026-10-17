# Documentation

Start with the repository [README](../README.md) for installation and a quick
example. The guides below describe current use and maintenance; dated records
identify the revisions and environments that were actually validated.

## User guides

| Document | Purpose |
| --- | --- |
| [Usage](usage.md) | Calculator configuration, examples and output reading |
| [Migration](migration.md) | Installing the independent package and adapting ABACUS/ATST/Forge callers |
| [Compatibility and CI](compatibility-ci.md) | Supported engine snapshots, current checks, gaps and acceptance links |
| [Changelog](../CHANGELOG.md) | User-visible changes and candidate/release status |

## Development

| Document | Purpose |
| --- | --- |
| [Contributor and agent entry](../AGENTS.md) | Project goal, upstream/downstream boundaries and working rules |
| [Contributing](../CONTRIBUTING.md) | Development setup, tests, package checks and review |
| [Design](design.md) | Agreed package responsibilities and architectural constraints |
| [Module reference](reference.md) | Runtime modules and legacy/latest output-format details |
| [Source provenance](../UPSTREAM.md) | Original authorship, imported revisions and subsequent adaptations |
| [Upstream integration audit](upstream-integration.md) | Dated ABACUS/ATST source comparison and reader-isolation rationale |

## Plans and evidence

- [Dual-engine CI follow-up](superpowers/plans/2026-10-17-dual-engine-ci.md):
  remaining portable-harness, build, PR-gate and engine-side adoption work.
- [ABACUS/ATST integration acceptance](superpowers/plans/2026-10-17-abacus-atst-integration-acceptance.md):
  local acceptance evidence, tested revision tuples and remaining rollout gates.
- [Standalone bootstrap](superpowers/plans/2026-10-16-standalone-bootstrap.md):
  original extraction and package-validation record.
- [Cross-repository regressions](superpowers/plans/2026-10-16-cross-repository-regressions.md):
  initial installed-consumer tests and source-integration evidence.

Keep current instructions in their owning guide and link to detailed evidence
instead of copying execution history into user documentation. Historical
results do not automatically validate a later package or engine revision.
