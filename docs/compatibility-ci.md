# Compatibility checks across repositories

## Current checkpoint

Release 1.2.1 is [published on PyPI](https://pypi.org/project/abacuslite/1.2.1/)
(2026-10-20, UTC+08:00). It preserves standard ASE energy values and adds
explicit no-entropy metadata for ATST's reference-only comparison. Both
installed-package lanes, both ATST/Forge consumer lanes and the develop/LTS
real-engine checks passed on the exact release tag
([39358708884](https://github.com/QuantumMisaka/abacuslite/actions/runs/39358708884)).
The [publish run](https://github.com/QuantumMisaka/abacuslite/actions/runs/39359654717)
uploaded that run's artifacts without rebuilding; both PyPI hashes match.
See the [1.2.1 record](superpowers/plans/2026-10-20-1.2.1-release.md) for
source, artifact, review and indexed-install evidence. The
[1.2.0 record](superpowers/plans/2026-10-19-1.2.0-release.md) remains historical.
Plugin main requires the GitHub Actions `compatibility-gate`, including for
administrators, with branches required to be up to date. Upstream ABACUS
adoption remains a separate open PR.

| Layer | Local candidate state | Remaining work |
| --- | --- | --- |
| Wheel/sdist and offline contracts | `1.2.1` tag run passed both package lanes and the aggregate gate; published PyPI digests match the tag artifacts and a fresh indexed install passed | Release acceptance complete for 1.2.1 |
| Installed ATST/Forge consumers | External-only Python 3.10/minimum and 3.12/current matrix passes locally and remotely; pins moved to ATST `v2.3.0` tag commit `b8c3218` (requires `abacuslite>=1.2.0,<2`) and Forge `d8d1a74` (`[abacuslite]` extra pins `1.2.0`) | Keep consumer pins aligned with abacuslite releases |
| Develop/LTS real engines | Fresh Ubuntu builds and all nine required checks per engine pass locally and remotely; the engine-side harness is ready for external-only adoption | Upstream ABACUS PR and its required-check configuration |
| Merge enforcement | Plugin main requires the successful aggregate from GitHub Actions, with strict freshness and administrator enforcement | ATST required-check configuration remains a separate maintenance decision |

Exact revisions, environments, raw-output links and earlier GPU/consumer runs
are in the [acceptance record](superpowers/plans/2026-10-17-abacus-atst-integration-acceptance.md).
The [dual-engine CI plan](superpowers/plans/2026-10-17-dual-engine-ci.md) defines
implementation and rollout steps. The [post-release execution record](superpowers/plans/2026-10-18-atst-next-actions.md)
tracks the current candidate and separates local, hosted and upstream states. Historical failures and detailed
run sequences stay in those records.

## Package and installed-consumer workflow

The `Package tests` workflow (`.github/workflows/tests.yml`) defines
push/PR checks without path filters, manual candidate runs and a weekly schedule:

- `installed-package` builds wheel/sdist, checks metadata, installs the wheel
  and runs offline regressions on Python 3.10/minimum and 3.12/current
  dependencies outside the checkout. The minimum lane pins ASE 3.28.0,
  NumPy 1.26.0, seekpath 2.2.0 and pytest 8.0.0. It also rebuilds a wheel
  from the sdist and tests it using the sdist's own tests/examples/configuration.
- `installed-consumers` installs the current plugin wheel and selected ATST
  wheel in external-only Python 3.10/minimum and 3.12/current environments.
  The minimum consumer lane uses pytest 8.4.0 to satisfy ATST's test extra;
  the package-only lane retains its pytest 8.0.0 floor. The runner verifies
  full collection/outcomes, expected skip reasons, package identity and
  deterministic output facts. It clears inherited pytest selectors and
  rejects deselection. The runner starts outside checkouts;
  ATST pytest uses repository fixtures with installed imports attested at both
  ends and in child processes. Forge is installed afterward under the same
  dependency constraints. The previous paired vendored/external acceptance
  remains historical evidence; the new ATST candidate keeps thin import
  forwarders and no duplicate parser implementation.
- Plugin-owned consumer tests then run outside checkouts. They cover input
  preparation, ordered SCF forces/Fermi values, periodic frame matching,
  fail-closed handoff, native-MD geometry, mixed-reader isolation, repeatable
  reads, constant-potential guards and Forge fact projection. Engine subprocesses
  are replaced in these offline tests; parsers are not each other's oracle.
  `.github/consumer-cases.json` lists all required case identities: missing,
  duplicate, extra, failed or skipped cases fail the report gate.
- `resolve-engine-refs` records one engine/harness/asset tuple for the run;
  `engine-compatibility` cold-builds both engines on Ubuntu 24.04 with two
  workers, installs the candidate wheel, and runs the reviewed ABACUS harness.
  Build provenance, runtime reports and raw files are uploaded on failure too.
- `compatibility-gate` runs even when prerequisites fail or are skipped and
  requires successful package, consumer, ref-resolution and real-engine jobs.
  A skipped engine lane cannot produce a passing aggregate.

After installing the candidate wheel and both consumers, run the plugin-owned
contracts from a copied test tree outside checkouts:

```bash
python -m pytest tests/consumers --run-consumers -q -s
```

Ordinary pytest skips consumers; explicit opt-in must fail if a consumer is
missing. Consumer dependencies do not become plugin runtime dependencies.
See [Contributing](../CONTRIBUTING.md) for package setup and verification.

PR jobs pin the ATST `v2.3.0` tag commit `b8c3218` and Forge `d8d1a74` in
`.github/workflows/tests.yml`. Weekly checks follow ATST and Forge `main`;
manual runs accept `atst_ref` and `forge_ref` for coordinated candidates.
Candidate pins must be publicly fetchable before a hosted run is accepted.
Weekly checks supplement PR checks.

## Develop and LTS engine coverage

LTS compatibility through `legacyio` is a plugin responsibility even though
LTS has no `interfaces/` tree or ASE-plugin workflow. Calculators bind reader
selection to their configured executable's actual version; creating a develop
calculator must not alter an existing LTS instance. Explicit readers remain
available for pure I/O. LTS has no socket driver; the shared harness supplies
its legacy-format oracle.

Local installed-wheel acceptance used plugin `ba65f606`:

| Engine snapshot | Reader | Real CPU/MPI interface checks |
| --- | --- | --- |
| develop `73cd094` (v3.11.0-beta10) | `latestio` | SCF, ASE relax/MD, native MD, band, magnetic and socket: 9 passed |
| LTS `725bf47` (v3.10.1) | `legacyio` | SCF, ASE relax/MD, native MD, band and magnetic: 8 passed |

A seeded LTS native-MD case with engine-generated velocities also passed.
Native-MD checks verify STRU velocity units, actual motion and each frame's
raw energy, cell, positions, forces and PBC. LTS's tested engine lacks the socket
driver. These short interface checks do not establish scientific convergence,
equivalence between engine versions or support for every engine feature.
See [repaired-wheel acceptance](superpowers/plans/2026-10-17-abacus-atst-integration-acceptance.md#repaired-wheel-acceptance)
for full engine/wheel identities, failures, repairs and retained output.

The new engine jobs use the stronger ABACUS-owned raw-property assertions,
independently of this package's imported opt-in tests. The manifest
`tests/engine-refs.json` pins engines, the reviewed harness and curated asset
hashes. Weekly runs resolve develop/LTS heads once; manual runs may select
`develop_ref`, `lts_ref` and `harness_ref`. The harness accepts an explicit
engine, MPI command, assets, format, wheel, report directory and installed
Python environment. It rejects wrong module origins, wheel/runtime mismatch,
wrong reader selection and incomplete case execution. LTS requires its eight
ordinary checks plus the seeded native-MD case; absent socket support is a
documented boundary, not a substitute for one of those checks.

The ABACUS target defined in
[issue #8165](https://github.com/deepmodeling/abacus-develop/issues/8165) is
fully external: no submodule and no vendored plugin. `interfaces/ASE_interface`
keeps only the engine-side harness, and CI installs the published 1.2.0 wheel
or a reviewed candidate. The harness passed all nine develop checks and the
LTS external lane in the earlier candidate `e446bda`; that candidate also
exercised a now-retired bundled lane. The current `tests/engine-refs.json`
tuple pins the harness and the develop engine to the reviewed ABACUS PR #8175
head `1bf602a` as a pre-merge candidate, with `engine_repository` still
`deepmodeling/abacus-develop`; both must be rebound to the merged upstream
commit after #8175 merges. The
[LTS hosted run](https://github.com/QuantumMisaka/abacus-develop/actions/runs/39059239649)
passed its external lane, and all 425 retained raw-file hashes were checked
after download. External-only ABACUS adoption is a separate upstream PR.

The final [ATST candidate run](https://github.com/QuantumMisaka/atst-tools/actions/runs/39060138450)
passes all six jobs at `edfd8f4`. A separate SAI run (`1835021`) validates 13
bounded workflow cases with installed external abacuslite, including restart
continuity and serial/parallel NEB. Initial MD evidence is snapshotted before
restart and checked from the returned archive. Sella, CCQN and descent IRC
complete at one step with `converged=false`; Dimer and scientific convergence
remain outside this acceptance. That GPU run uses the recorded `4b92455`
engine plus a v3.10.1 legacy smoke; it does not replace the fresh CPU matrix.

## Repository responsibilities

Each changed repository should check its own candidate against tested partners.
The rows below describe the target; external-only ABACUS adoption and upstream
merge enforcement remain separate upstream decisions.

| Changed repository | PR verification |
| --- | --- |
| abacuslite | Current PR wheel, own contracts, installed consumers and pinned develop/LTS engines |
| ABACUS | This PR's engine, a validated plugin, and engine-owned assertions/assets; retain failed outputs |
| ATST | This PR's ATST with the supported external plugin; profile, I/O and affected workflow checks |
| Forge | This PR's Forge with the optional plugin; preserve native-default and read-only projection contracts |

Coordinated runs select both candidate revisions explicitly. Scheduled
engine checks follow develop/LTS heads, supplementing stable PR baselines.
ABACUS adapters may forward imports/configuration but must not duplicate the
parser. ATST's candidate forwards supported historical import paths to the
installed external package, including shared module state.
Ordinary community PRs must not submit HPC jobs; expensive workflow acceptance
runs only through a maintainer-controlled entry on trusted infrastructure.

## Coordinated changes and enforcement

Preserve public imports, units, atom ordering, missing values, supported formats,
read-only artifacts and consumer handoff. Internal refactoring is welcome;
coverage totals and source hashes alone cannot establish correct behavior.
Intentional breaks need an explicit contract, migration and versioning decision.
Do not weaken tolerances or references merely to accept a refactor.

Keep counterpart refs fetchable, retain resolved revision tuples and logs, and
validate candidate pairs before changing dependency constraints. Publish the
verified plugin before switching stable consumers to its indexed version.
Fork PR execution stays read-only: no release/HPC secrets or privileged
`pull_request_target` execution of candidate code.

The required `compatibility-gate` covers package, consumer, resolved-ref and
dual-engine jobs. A real hosted consumer failure produced a failed aggregate;
the repaired run passed all eight jobs. Branch protection requires that check
from the GitHub Actions app (ID 15368), uses strict freshness, applies to
administrators, and disallows force pushes and branch deletion. Keep this
configuration aligned with the workflow; a green job alone does not enforce
merge blocking. Review workflow
changes that could remove the gate. If merge queues are introduced, add the
`merge_group` trigger before requiring checks there. Upstream ABACUS
branch-protection details were unavailable to the inspecting account, so its
required-check enforcement remains unconfirmed. The plugin protection change belongs to this post-release
CI rollout. The separate GitHub `pypi` environment still only accepts
deployments from main; published 1.2.0 artifacts and its tag are unchanged.

GitHub references:
[required checks and skipped workflows](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks),
[protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches),
[privileged PR workflow security](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target).
