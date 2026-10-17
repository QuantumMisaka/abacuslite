# Post-release ATST and engine integration

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

- W1 local checks passed: `git cat-file` rejects the runner path on ATST
  `origin/main`; the public integration ref resolves to `87caeedb`. Interim
  scheduled ref and consumer result checks are implemented. All 14 guard
  regressions passed, the retained ten-case tag report was accepted, and
  actionlint passed. Hosted workflow verification remains pending.
- W2 in progress: portable harness and clean build packages delegated; workflow
  integration is controller-owned. No remote engine gate is claimed yet.
- W3a complete; W3b candidate implementation in progress. No consumer main-branch
  integration or ATST release has occurred in this continuation.
- W4 pending local acceptance and hosted verification.
- W5 minimum consumer lane can proceed with W3b; runtime rows follow the
  verified candidate and site-specific execution requirements.

Raw controller evidence is retained in
`/home/james/scratch/abacuslite-post-release-20261018/`; package-specific build
and runtime directories will be recorded as they are produced.
