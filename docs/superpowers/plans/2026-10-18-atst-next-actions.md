# Post-release ATST and engine integration

> Status (2026-10-19): ATST external-only integration merged to `main` at
> `49c8626` (2.3.0); merged candidate branches were removed. ABACUS
> external-only adoption and the socket contract remain a separate upstream PR.

## Scope and decisions

The maintainer requested continuation with `subagent-driven-development` on
2026-10-18, after abacuslite 1.1.0 was published and its indexed installation
verified. This executes the existing [package design](../../design.md),
[integration acceptance](2026-10-17-abacus-atst-integration-acceptance.md) and
[dual-engine CI plan](2026-10-17-dual-engine-ci.md). Validate locally before
remote candidate runs or PR delivery. Upstream adoption and new consumer
releases remain distinct from candidate implementation and verification.

The working copy of the next-actions draft in the main checkout is preserved.
This English execution revision retains its W1–W5 scope and r3 decisions.
Independent plan review on 2026-10-18 confirmed that the two earlier findings
were resolved: external-only migration is now selected, and individual workflow
acceptance/deferment is explicit. No Important plan blocker remained.

Ruling: new ATST candidates depend on external abacuslite only, retaining thin
forwarders for supported historical imports — this implements the approved
single-source design and avoids maintaining two parsers — missed historical
imports would break callers, so forwarding and installed-consumer regressions
must pass before production integration. The last paired vendored/external
acceptance remains historical audit evidence, not a live lane.

No new physics features, ATST workflow redesign, Forge protocol changes or
Paimon v2 production edits are part of this work. Dimer and scientific
convergence studies are explicitly deferred below. Release 1.1.0 and its tag
must remain immutable.

## Work packages and acceptance

### W1: Scheduled consumer ref and complete coverage

- Until the ATST integration reaches main, use a fetchable integration ref for
  scheduled checks. Preserve explicit manual candidate selection.
- Print the resolved SHA and fail clearly if the selected ATST tree lacks
  `scripts/run_abacuslite_consumer.py`.
- Verify the expected plugin-owned consumer case identities in the JUnit
  report. Missing, duplicate, unexpected, failed or skipped required cases
  fail acceptance. Update the manifest alongside reviewed behavioral changes;
  the manifest protects coverage, not immutable test implementation.
- Record the selected ATST source and installed wheel identity.

Acceptance: the selected ref resolves, the actual runner executes, all required
consumer cases pass, and missing-runner/reduced-coverage negatives fail.

### W2: Portable dual-engine CI and aggregate gate

Implement Tasks 1–3 of the [dual-engine plan](2026-10-17-dual-engine-ci.md) in
full: a shared ABACUS-owned two-format harness, a clean CPU build recipe, and
an unprivileged plugin workflow consuming its own candidate wheel. Preserve
develop 9 checks and LTS 8 plus the seeded LTS native-MD case. Record LTS's
absent socket driver explicitly; do not turn required legacy coverage into
skips. Preserve independent raw-property assertions, strict velocity units,
per-frame geometry/forces/PBC, actual displacement, magnetic/band facts and
bounded socket shutdown.

Use explicit engine paths, MPI command, assets, format, wheel and report
directory. Check actual version, installed module origin, wheel/runtime bytes
and reader selection. Keep raw failures/timeouts and machine-readable results.
Pin reviewed engine/harness sources for PRs; weekly runs resolve branch heads.
Build CPU/LCAO engines in a clean Ubuntu 24.04 environment with GNU/OpenMPI,
FFTW/OpenBLAS/ScaLAPACK and two build workers. Measure a cold build within the
120-minute bound before adding a cache. Frozen local engines alone do not
establish a clean dependency recipe or hosted runner success.

Acceptance: the full case sets pass through portable entry points, wrong
imports/readers/velocities/MD scaling and failed/timed-out engines fail their
own checks, and failed/skipped engine jobs fail the aggregate gate. Record
local clean builds and actual remote runs separately.

### W3a: Published package — complete

1.1.0 is available on PyPI. Both registry hashes match the tag CI artifacts;
fresh indexed installation, dependency checks and 148 offline tests passed.
See the [release record](2026-10-17-1.1.0-release.md). Do not retry upload.

### W3b: ATST external-only migration

- Declare the supported abacuslite dependency, retain ATST launcher/workflow
  policy, and replace the duplicate vendored implementation with thin
  compatibility imports. Preserve known Paimon direct I/O import paths.
- Migrate ATST CI/runner and plugin consumer CI together to one external lane.
  Preserve installed-wheel provenance, child-process source-shadow checks,
  nonempty complete test execution and independent behavior assertions.
- Archive the last paired acceptance identities. Do not compare different ATST
  versions under the former same-wheel equality contract.
- Update current installation/development documentation without claiming a new
  ATST release. Keep a missing or broken required plugin failure explicit.

Acceptance: installed `BACKEND_SOURCE == "external"`, historical imports still
work, full external suites and the complete consuming workflow pass on minimum
and current environments, and removed vendored-only tests have an explicit
coverage disposition. Production integration follows W2 and cross-repository
acceptance; PyPI availability alone is insufficient.

### W4: References, engine-side checks and merge enforcement

- Publish locally verified candidate refs in dependency order and confirm
  public fetchability before hosted runs. No automatic upstream PR submission.
- Update the ABACUS develop external lane from the old plugin source to the
  reviewed stable package. Verify that lane uses its candidate's own engine
  and supported socket checks. Record bundled defects rather than weakening
  stronger external assertions.
- Prepare the LTS engine-PR workflow using the external reviewed harness,
  without backporting interfaces. Its community adoption is a separate status.
- After the complete plugin gate succeeds remotely, configure it as a required
  main-branch check and verify the effective rule. Inspect ATST/ABACUS branch
  enforcement and merge-queue requirements; do not claim control of upstream
  settings or adoption that has not occurred.

Acceptance: every pin resolves, candidate versus upstream state is explicit,
negative required checks block ordinary merging under the configured rule,
and remaining external dependencies have a named status.

### W5: Consumer matrix and bounded runtime coverage

Add Python 3.10/ASE 3.28 to installed ATST/Forge coverage. Keep archived rc1
artifacts separate from current builds and move obsolete local distributions
to scratch if necessary. New diagnostics/docstrings are English; inspect
existing language debt and use a focused follow-up rather than changing the
immutable release. Preserve real-engine scripts in source control and raw
evidence in controlled artifacts.

| Workflow | This round | Observable acceptance | Scientific convergence |
| --- | --- | --- | --- |
| Relax | Revalidate candidate wheel | Real engine finishes; finite energy/forces and expected outputs | Deferred |
| MD/restart | Revalidate candidate wheel | Resume from retained state; check restart step/geometry and energy continuity using existing case tolerances | Deferred |
| NEB | Revalidate candidate wheel | Actual workflow finishes with image/barrier artifacts | Deferred |
| Constant potential | Revalidate candidate wheel | Actual workflow finishes with potential and expected outputs | Deferred |
| Dimer | Explicitly deferred | Excluded from completion claims | Deferred |
| Sella TS | Execution only | Workflow completes and emits its TS candidate; imaginary-mode validation deferred | Deferred |
| CCQN | Execution only | Workflow completes and emits chain/result artifacts | Deferred |
| IRC | Execution only | Workflow completes and emits endpoint frames | Deferred |

Do not use one workflow result to close other rows. Record inherited runtime
blockers and result scope honestly; no scientific convergence claim follows
from workflow execution alone.

## Ownership and recovery

- Controller: this record, plugin workflow/consumer guards, cross-repository
  coordination, review, hosted acceptance and enforcement status.
- ATST implementer: isolated `atst-tools-abacuslite-integration`, initial
  `98f9a16b5fda6b35e8f7aed440fa631a0640d96c`; owns ATST dependency, forwarding,
  runner/workflow, affected tests and documentation.
- ABACUS implementer: isolated `abacus-develop-abacuslite-review`, initial
  `bca816410dcd8e380f2d84306c3e317e9d3b0716`; owns portable harness and
  engine-side candidate lanes. Merge current develop without rewriting history.
- Build implementer: only plugin `scripts/ci/build_abacus.sh`, dependency setup
  script, engine reference manifest and their build-guard tests. The controller
  serializes the shared plugin Git index.
- Plugin initial revision: `4215b712c0651b0d5bbed1e1ae16abe49d1a0420` in existing
  `abacuslite/.worktrees/cross-repo-ci`. Main-checkout untracked draft/review
  material and ABACUS main-checkout user edits remain untouched.

Fresh fetch on 2026-10-18 resolves ATST main `1081b9d1`, ABACUS develop
`73cd0943` and LTS `725bf475`. Implementation and independent review use each
package's full initial-revision-to-final diff and its retained raw evidence.

## Execution record

Acceptance on 2026-10-18 (UTC+08:00): implementation, selected independent
reviews, local verification and hosted candidate runs all passed. The released
1.1.0 tag and its PyPI artifacts remain unchanged. Consumer production adoption,
community PR delivery and the next Forge work remain separate follow-ups.

| Package | Verified outcome |
| --- | --- |
| W1 | Public ATST candidate ref, explicit missing-runner failure and exact ten-case consumer gate; both hosted consumer lanes pass |
| W2 | Portable develop/LTS harness, clean CPU build helpers, source/asset/wheel provenance and required aggregate implemented; fresh local and hosted engine lanes each pass 9/9 |
| W3a | 1.1.0 publication remains complete; no upload repeated |
| W3b | External-only ATST dependency with historical import forwarders; full installed suites, four Python/ASE lanes and provenance checks pass; consumer main remains unchanged |
| W4 | Public candidate refs and engine-owned develop/LTS workflows pass; plugin main requires the successful aggregate with strict freshness and administrator enforcement |
| W5 | Exact minimum/current consumer environments pass; SAI job 1835021 passes all 18 stages and 13 bounded cases with retained, independently reviewed raw evidence |

### Reviewed sources and hosted runs

| Repository / candidate | Revision | Hosted evidence |
| --- | --- | --- |
| Plugin CI | `6de3b83677f6a5cc82a47dbf05e9b6c6b9b2ef55` | [39059543765](https://github.com/QuantumMisaka/abacuslite/actions/runs/39059543765): all eight jobs pass |
| ATST external dependency and runtime harness | `edfd8f436d2bca6cc26b186b39a70f53e790e686` | [39060138450](https://github.com/QuantumMisaka/atst-tools/actions/runs/39060138450): all six jobs pass |
| ABACUS develop harness and candidate lanes | `e446bda12f852a29d9cffd883ef29642e83cc6a6` | [39058538488](https://github.com/QuantumMisaka/abacus-develop/actions/runs/39058538488): bundled and external each 9/9 |
| ABACUS LTS external-harness workflow | `00028595fad799370e9cd1d5fe35abffa3b0ed75` | [39059239649](https://github.com/QuantumMisaka/abacus-develop/actions/runs/39059239649): external legacy 9/9 |

The ATST candidate was merged to `main` at `49c8626`; the plugin workflow now
pins that commit and the weekly schedule follows `main`. The ABACUS harness
candidates remain `integrate/abacuslite-portable-ci` and
`integrate/abacuslite-lts-ci` on the personal fork until the external-only
upstream PR is reviewed.

### Local and returned-artifact verification

- All 46 plugin CI-helper regressions and actionlint pass. Independent code
  review covered the complete plugin change and the pip provenance repair.
- Exact minimum/current consumer environments each collect all 1408 ATST
  tests: 1373 pass, 35 expected skips, zero deselection/failure. Two skips are
  artifact-inspection opt-ins not enabled in those lanes; earlier reports with
  wheel/sdist variables set have 33 skips. All ten plugin-owned cases pass in
  each environment. The frozen verifier also accepts both downloaded hosted
  consumer reports and their exact ten-case JUnit reports.
- Fresh Ubuntu 24.04 Docker builds with two workers take 733 seconds for
  develop and 511 seconds for LTS, followed by all nine checks per engine.
  The controller verifies all 367 retained build/runtime artifact hashes.
  The successful hosted plugin run builds develop in 388 seconds and LTS in
  349 seconds, then passes all required cases. Its 283 raw-file hashes and
  candidate-wheel identity were verified after download. All eight installed
  plugin runtime files match the published wheel byte for byte.
- The ABACUS candidate workflows additionally pass their own engine revisions;
  the controller verifies all 425 downloaded raw-file hashes across develop
  bundled, develop external and LTS external lanes.
- SAI job `1835021` completes `0:0` in 11m21s on two V100 GPUs. Independent
  review confirms 18 successful stages, 13 passing workflow cases, installed
  wheel provenance, exact restart geometry/energy continuity and subsequent
  motion from actual trajectories. All five retained harness files match
  `edfd8f4`; six initial-MD snapshots have verified hashes and literal energies.
  Sella, CCQN and two-direction descent IRC report `converged=false` at one
  step. Dimer and scientific convergence remain explicitly deferred.

### Repairs closed during acceptance

- ABACUS CI now executes the newly built binary, checks the installed entry's
  hash, propagates failures from login shells and kills surviving process-group
  descendants after timeout. All three findings passed incremental review.
- ATST clears inherited pytest selection options, rejects deselections and
  starts a fresh attestation for retries at the same report path. Controlled
  filtered/retry negatives and full installed reruns close both findings.
- The first plugin hosted run `39059108288` passed both engines but correctly
  failed its aggregate when Python 3.10's bundled pip 23.0.1 omitted a local
  wheel archive hash. A real pip 23.0.1 reproduction confirms the cause;
  explicit wheel URLs carrying SHA256 preserve provenance and reject a wrong
  digest. Local full-suite verification and the next hosted run pass.
- First SAI run `1834789` passed runtime assertions, but restart overwrote its
  initial raw log. The revised auditor rejects that archive. Immutable initial
  snapshots and the complete replacement run `1835021` close the retention
  gap; run-1 is retained as failure evidence rather than relabeled as final.

### Rollout, preservation and remaining scope

The GitHub API confirms plugin main requires `compatibility-gate` from GitHub
Actions app 15368, strict up-to-date checks, administrator enforcement, and no
force pushes or branch deletion. The aggregate's failed/skipped/cancelled/
missing-result negatives pass locally; the first hosted failure demonstrates
remote failure propagation. Rule enforcement is verified through the returned
configuration. The workflow includes `merge_group` for future merge queues.

Ruling: use the reviewed isolated plugin branch for the main CI rollout so the
default PR and scheduled workflows receive the verified gate. Preserve the
main checkout's uncommitted alternative W1 workflow, expected-case list and
original draft/review notes in place; do not overwrite them when updating the
remote branch. Consumer and ABACUS branches remain reviewable candidates.
No upstream PR, consumer main merge, new ATST release or Forge implementation
change is performed in this continuation. ATST main currently has one required
review but no status checks in the inspected response. Upstream ABACUS branch
protection is unconfirmed (API 404); community adoption and enforcement require
separate follow-up.

Obsolete rc1 distributions from both plugin checkouts were moved to
`/home/james/scratch/abacuslite-archived-dist-20261018/` with a hash manifest.
Existing non-English diagnostics in the released runtime remain follow-up
work. SAI's full persistent-storage quota required streaming payload/results
through compute-node `/tmp`; the fixed GPU engine is `4b92455`, not the latest
CPU develop source. The GPU checks supplement the fresh CPU matrix.

### Retained evidence

- Controller checks, downloaded hosted reports and branch-protection records:
  `/home/james/scratch/abacuslite-post-release-20261018/`.
- Clean engine build/runtime reports and all local hashes:
  `/home/james/scratch/abacuslite-dual-engine-build-20261018/`.
- Portable harness repair evidence:
  `/home/james/scratch/abacuslite-portable-harness/review-fixes/`.
- Final SAI evidence:
  `/home/james/scratch/abacuslite-atst-runtime-20261018/candidate-run-2/`;
  result archive SHA256
  `429001446a5fc83409cbfd96c3a833215278080955f1b0a0f6e881de302f1717`.
- ATST production wheel SHA256:
  `5cbce59082fddb6d4382602995fdb264531df35d3edb7978fde61907bcdb6270`.
- Published plugin wheel/source identities remain in the
  [release record](2026-10-17-1.1.0-release.md).
