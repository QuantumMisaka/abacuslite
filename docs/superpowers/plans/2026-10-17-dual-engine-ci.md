# Develop/LTS engine CI follow-up

## Goal and current status

On 2026-10-17 the maintainer asked how to close the real-engine CI gap and
improve the README. This is the implementation sequence for the remaining CI
work under [the package design](../../design.md) and the existing
[ABACUS/ATST acceptance plan](2026-10-17-abacus-atst-integration-acceptance.md).
It preserves the instruction to validate locally before proposing PRs.
The new jobs described here are not yet implemented or remotely active.

The local candidate `ba65f606` passes current develop
`73cd094361f77574f9b28e825913e00f1d2c742a` and LTS
`725bf475a7159db4c1890a1f55160393e14b6b13` interface checks. Scripts and raw
evidence are retained in
`~/scratch/abacuslite-current-branches-20261017/FINAL_REPORT.md`.
The scripts contain local paths and the LTS adaptation is only in scratch.
Simply adding `--run-engine` to the plugin workflow would neither reproduce
that acceptance nor supply its stronger assertions.

Ruling: ABACUS continues to own engine assertions, assets and independent
references. Make its existing harness portable across the two output formats;
the plugin checks out a reviewed harness revision separately from the engine
source. LTS needs no copied `interfaces` implementation. Keep parser code in
abacuslite and keep the integration harness out of the runtime wheel.

## Task 1: Preserve the verified two-format harness in source control

- [ ] Extend the develop candidate's `interfaces/ASE_interface/tests/` using
  the verified scratch changes. Share setup, provenance and assertions, with
  small explicit adapters for legacy headers/band tables and newer files.
  Do not duplicate a full parser or an entire test tree for LTS.
- [ ] Accept an explicit absolute executable, MPI launcher, asset directory,
  expected format and report directory. Remove workstation paths and symlink
  selection. Check actual engine `--version` and calculator reader selection;
  record engine/harness/plugin revisions, binary/wheel hashes, dependencies
  and installed module paths. Run copied tests outside package source trees.
- [ ] Preserve SCF energy/forces/stress/available Fermi level, relaxation/ASE
  MD handoff, band/magnetic facts and every native-MD frame's energy,
  geometry/forces/PBC. Assert STRU velocity units/order and real displacement;
  retain the seeded LTS generated-velocity case. Develop additionally runs
  socket with bounded shutdown. LTS's absent driver is a declared capability
  difference, not a blanket skip for legacy behavior. Keep frame-count
  expectations specific to the tested engine format.
- [ ] Preserve failures/timeouts and raw output; emit machine-readable results
  plus logs. Reject empty or incomplete ordinary lane selections.

Acceptance: the portable entry point reproduces develop 9 and LTS 8 tests plus
the seeded LTS case using the frozen binaries/wheel. Wrong source imports,
reader selection, STRU velocities, MD cell scaling and failed/timed-out engines
must each fail their owning checks. Reuse existing regressions and pre-fix
evidence where they protect the same behavior; do not loosen tolerances.

## Task 2: Build both engines on ordinary hosted CPU runners

- [ ] Add a CI build entry point and reviewed reference manifest in the plugin
  repository (proposed `scripts/ci/build_abacus.sh`, `tests/engine-refs.json`).
  Start with `ubuntu-24.04`, GNU/OpenMPI, FFTW, OpenBLAS and ScaLAPACK, two
  compile workers and MPI two-rank smoke cases. Verify the clean dependency
  recipe locally. No SAI credentials, private assets or custom image release
  are needed for this CPU scope.
- [ ] Preserve the tested minimal CPU/LCAO feature set and use the actual
  branch options: develop `ENABLE_ELPA=OFF`, LTS `USE_ELPA=OFF`, and their
  corresponding OpenMP options. Check configure diagnostics for unused flags.
  Bind tests to the produced executable by absolute path and hash, never an
  unrelated `abacus` discovered from PATH.
- [ ] Resolve refs once to full SHAs. Ordinary PRs pin the two tested engine
  SHAs above and a separately reviewed harness revision. Use common curated
  assets with recorded identity and verify all required files are present.
  Baseline updates go through reviewed compatibility changes.
- [ ] Measure a cold build/run with a 120-minute job bound before adding cache
  optimization. Include source, OS/toolchain, dependencies and build options
  in cache keys. Cache misses must still work; cached outputs retain provenance
  checks. Measure hosted resource requirements rather than assuming local
  build time or memory applies there.

Acceptance: both engines build/run in a fresh CI-like environment without
`/home/james` dependencies. Save configure/build/runtime logs, feature choices
and elapsed time. Existing local binaries validate harness behavior but do
not satisfy this clean-build requirement.

## Task 3: Gate the plugin PR's own wheel on both engines

- [ ] Extend `.github/workflows/tests.yml` with an `engine-compatibility`
  develop/LTS matrix consuming the same current PR wheel artifact from the
  package job. Keep existing package and ATST/Forge checks. Do not accidentally
  install plugin main or a published copy instead of the candidate wheel.
- [ ] Use `fail-fast: false`, upload logs/raw output with `if: always()`, and
  fail for missing assets/engines, failed builds, wrong imports, timeouts or
  skipped required lanes. Do not apply `continue-on-error` to required checks.
- [ ] Add this matrix to `compatibility-gate` dependencies. The stable gate
  runs with `always()` and accepts only successful package, consumer and
  engine jobs. Avoid PR path filters that omit required verification.
- [ ] Extend the weekly schedule to resolve develop/LTS heads while testing
  that scheduled plugin revision. This supplements fixed PR baselines.
  Manual runs may select explicit engine/harness refs for coordinated changes;
  record the resolved tuple in the summary.
- [ ] Keep fork PR execution unprivileged: `contents: read`, no persisted
  checkout credentials or release/HPC secrets. Pass ref inputs through action
  inputs or quoted environment variables, not interpolated shell source.

Acceptance: lint workflows/shells, run their actual entry points locally, and
exercise failed/skipped engine aggregation so passing offline checks cannot
hide a broken engine lane. Validate cold and cached execution when cache is
introduced. Actual remote Actions success remains a later checkpoint.

## Task 4: Protect engine changes and resolve cross-repository references

- [ ] Update the ABACUS develop external lane to a reviewed plugin commit
  containing the LTS/velocity repairs. Build this PR's engine and use the
  portable harness with explicit binary identity. Run supported socket checks
  in both transition lanes. If stronger assertions expose a bundled defect,
  retain and resolve that finding before claiming both lanes pass; do not
  weaken the external gate to match an existing defect.
- [ ] For LTS engine PRs, propose a lightweight workflow that checks out the
  reviewed external harness, installs the reviewed plugin and builds that
  LTS PR's own engine. No interface backport is needed. Upstream adoption is
  community work; until adopted, LTS engine-PR protection remains pending.
- [ ] Keep plugin/harness refs explicit for coordinated candidates. After
  publication a tested release may replace a source pin; the unpublished
  `1.1.0rc1` cannot currently serve as a PyPI dependency.

Local work proceeds through Tasks 1–3 and then engine-side lane verification.
Before remote runs, every candidate ref must be fetchable: the ATST `87caeedb`
consumer pin and new ABACUS harness currently depend on local candidates.
The 2026-10-17 GitHub commit API checks returned `422: No commit found` for
ATST `87caeedb`, plugin `ba65f606` and ABACUS fork harness `bca8164` in their
respective repositories; none can currently serve as a remote checkout ref.
When remote delivery is authorized, publish reviewed branches in dependency
order and verify checkout without private credentials. A reviewed personal-
fork harness ref can support plugin CI before upstream ABACUS merges it.

After local acceptance and review, remote candidate runs establish hosted-
runner evidence. PR delivery, PyPI publication and production cutover retain
their existing separate checkpoints. Required-check settings follow actual
successful runs on the intended refs. Record enforcement per repository and
branch: a green workflow alone does not block merges.

## Completion evidence

- The current plugin wheel passes both engines and existing package/consumer
  checks through version-controlled, portable entry points.
- Negative checks prove that wrong handoff and failed/skipped engine jobs
  cannot yield a successful required gate.
- Hosted CI has run the exact reviewed candidates; every checkout ref resolves.
- Required-check enforcement, upstream LTS workflow adoption, publication and
  dependency cutover each have their own status, independent of local results.

GitHub behavior references:
[workflow conditions and matrices](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax),
[required status checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks),
[dependency caching](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching).
