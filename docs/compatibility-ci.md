# Compatibility checks across repositories

## Current checkpoint

As recorded on 2026-10-17, the independent package remains an unpublished
`1.1.0rc1` candidate. Local package, consumer and real-engine acceptance exists.
The candidate cross-repository workflows have not run remotely, and the plugin's
dual-engine PR jobs are still planned. A successful local run, a workflow
implemented in a branch and an enforced merge check are separate outcomes.

| Layer | Local candidate state | Remaining work |
| --- | --- | --- |
| Wheel/sdist and offline contracts | Validated; package workflow defined | Deliver the reviewed candidate and inspect remote results |
| Installed ATST/Forge consumers | Validated; paired consumer workflow defined | Make candidate refs fetchable and run remote checks |
| Develop/LTS real engines | Validated for the snapshots below | Implement portable dual-engine PR jobs |
| Merge enforcement | Plugin protection absent at inspection; upstream enforcement unconfirmed | Activate appropriate required checks after successful remote runs |

Exact revisions, environments, raw-output links and earlier GPU/consumer runs
are in the [acceptance record](superpowers/plans/2026-10-17-abacus-atst-integration-acceptance.md).
The [dual-engine CI plan](superpowers/plans/2026-10-17-dual-engine-ci.md) defines
remaining implementation and rollout steps. Historical failures and detailed
run sequences stay in those records.

## Package and installed-consumer workflow

The candidate `Package tests` workflow (`.github/workflows/tests.yml`) defines
push/PR checks without path filters, manual candidate runs and a weekly schedule:

- `installed-package` builds wheel/sdist, checks metadata, installs the wheel
  and runs offline regressions on Python 3.10/minimum and 3.12/current
  dependencies. It also rebuilds a wheel from the sdist and tests it.
- `installed-consumers` uses the current plugin wheel and the same selected
  ATST wheel in separate vendored/external environments with identical base
  dependencies. It compares test collection/outcomes, skip reasons, package
  identity and deterministic output facts. The runner starts outside checkouts;
  ATST pytest uses repository fixtures with installed imports attested at both
  ends and in child processes. Forge is installed after this paired comparison.
- Plugin-owned consumer tests then run outside checkouts. They cover input
  preparation, ordered SCF forces/Fermi values, periodic frame matching,
  fail-closed handoff, native-MD geometry, mixed-reader isolation, repeatable
  reads, constant-potential guards and Forge fact projection. Engine subprocesses
  are replaced in these offline tests; parsers are not each other's oracle.
- `compatibility-gate` runs even when prerequisites fail or are skipped and
  requires successful package and consumer jobs. It currently has no real-engine
  dependency; adding one is part of the dual-engine plan.

After installing the candidate wheel and both consumers, run the plugin-owned
contracts from a copied test tree outside checkouts:

```bash
python -m pytest tests/consumers --run-consumers -q -s
```

Ordinary pytest skips consumers; explicit opt-in must fail if a consumer is
missing. Consumer dependencies do not become plugin runtime dependencies.
See [Contributing](../CONTRIBUTING.md) for package setup and verification.

PR jobs pin ATST `87caeedb` and Forge `43f5d4a`; the weekly schedule uses their
`main` heads to detect drift. Baselines can be updated through tested changes.
Manual runs accept `atst_ref` and `forge_ref` for coordinated candidates.
The ATST pin is still local at this checkpoint, so remote checkout cannot work
until that commit is published. Weekly checks supplement PR checks.

## Develop and LTS engine coverage

LTS compatibility through `legacyio` is a plugin responsibility even though
LTS has no `interfaces/` tree or ASE-plugin workflow. Calculators bind reader
selection to their configured executable's actual version; creating a develop
calculator must not alter an existing LTS instance. Explicit readers remain
available for pure I/O. LTS has no bundled-plugin comparison baseline.

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

The plugin workflow currently runs offline legacy/latest regressions, including
real LTS output fixtures; it does not pass `--run-engine`. Simply enabling its
imported integration tests is insufficient: some only print an energy or check
file existence. Reuse the stronger ABACUS-owned raw-property assertions.

Upstream develop tests its bundled plugin. Our local `bca8164` candidate adds
an external wheel lane but still pins old plugin `dc02043`; it needs the reviewed
repair revision, explicit newly built binary identity and matching supported
socket coverage. LTS needs a lightweight external-harness workflow, without
backporting the interface implementation. These are pending changes.

## Repository responsibilities

Each changed repository should check its own candidate against tested partners.
The rows below describe the target; engine-side adoption and remote candidate
verification remain incomplete.

| Changed repository | PR verification |
| --- | --- |
| abacuslite | Current PR wheel, own contracts, installed consumers and pinned develop/LTS engines |
| ABACUS | This PR's engine, a validated plugin, and engine-owned assertions/assets; retain failed outputs |
| ATST | This PR's ATST with the supported external plugin; profile, I/O and affected workflow checks |
| Forge | This PR's Forge with the optional plugin; preserve native-default and read-only projection contracts |

Coordinated runs select both candidate revisions explicitly. Planned scheduled
engine checks follow develop/LTS heads, supplementing stable PR baselines.
ABACUS adapters may forward imports/configuration but must not duplicate the
parser. ATST's vendored lane is transitional until direct callers migrate.
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

After remote verification, require the stable aggregate gate on the intended
branches; a green job alone does not enforce merge blocking. Review workflow
changes that could remove the gate. If merge queues are introduced, add the
`merge_group` trigger before requiring checks there. Upstream branch-protection
details were unavailable to the inspecting account; visible rules do not prove
an enforced abacuslite gate. No branch settings were changed by this work.

GitHub references:
[required checks and skipped workflows](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks),
[protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches),
[privileged PR workflow security](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target).
