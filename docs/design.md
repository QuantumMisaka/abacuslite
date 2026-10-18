# Independent ASE plugin

The maintainer approved establishing `QuantumMisaka/abacuslite` and continuing
implementation on 2026-10-16. This repository owns the installable plugin;
ABACUS retains engine integration tests, and ATST and Forge consume its package.

The initial implementation preserves `Abacus`, `AbacusProfile`, `AbacusSocketIO`,
and the existing `abacuslite.io` and `abacuslite.utils` module paths. Source
layout changes must not be combined with an unrelated API rewrite. Preserve
upstream socket support and diagnostics while merging ATST's general-purpose
SCF frame, Fermi-level and point-KPT corrections.

I/O functions remain independent of engine execution. Output parsing is
read-only and repeatable. A calculator's choice of legacy/latest output reader
must not change when another calculator is constructed. Existing reader
functions remain available for consumers that explicitly select a format.

ATST workflow configuration and orchestration remain outside this project.
Forge's native default, optional parser and fact projection are unaffected.
ABACUS's bundled `interfaces/ASE_interface` is expected to be replaced by this
package; the compatibility and migration records track that rollout.

Package, engine and output-format versions are distinct. Version 1.1.0 is
published on PyPI and validated by package, consumer and real-engine checks.
See the [compatibility record](compatibility-ci.md) for tested snapshots and
remaining gaps.

Use one source implementation. Existing consumers must migrate direct vendored
imports before their copies are removed; temporary compatibility modules may
forward to this package but must not retain a second implementation.

Source provenance is recorded in [UPSTREAM.md](../UPSTREAM.md). The initial
snapshot commit preserves the imported tree; later commits separate packaging
and behavior adaptations. No automatic PyPI publication is enabled by bootstrap.
