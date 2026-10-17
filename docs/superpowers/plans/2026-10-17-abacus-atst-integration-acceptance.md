# ABACUS and ATST integration acceptance

## Goal and scope

The maintainer requested on 2026-10-17 that integration be established against
the latest ABACUS `develop` and ATST `main`, and that both integrations be
completed before returning to Forge. This plan implements that ordering under
[the independent-plugin design](../../design.md) and
[the compatibility strategy](../../compatibility-ci.md).

This document records the execution sequence and inspected readiness.
Its checkboxes distinguish preparation from implementation and acceptance.
PyPI publication still requires the maintainer's release authorization after
the concrete candidate and evidence are ready. No Forge changes are included.

**Earlier local acceptance passed for the 2.2.8 tuple on 2026-10-17.** Package installation, both ABACUS
CPU lanes, ATST offline/installed checks and the scoped trusted GPU workflows
have verified evidence. Remote CI, PR delivery, publication and production
dependency cutover remain pending. The maintainer's local-validation-first
instruction is honored by retaining the candidate branches locally at this
checkpoint; the broader completion gate below is not yet met.

## Refreshed baselines and preflight

Fetched from the authoritative remotes on 2026-10-17:

| Component | Branch / revision | Role |
| --- | --- | --- |
| `deepmodeling/abacus-develop` | `develop`, `4b92455cab1b1a51e8534b7eb869798ae1241b1b` | Engine and engine-owned integration harness |
| `QuantumMisaka/atst-tools` | `main`, `45d8c78de8a605c127cd4c36742d0c9525a0a6b6` | Workflow consumer |
| `QuantumMisaka/abacuslite` | `main`, `136783baf4b6832c13d02a2542753439fbacc6df` | Initial candidate package, `1.1.0rc1` |

The remote branch heads did not change from the previous audit. Refresh again
before final acceptance and integration; merge relevant upstream changes into
the candidate branches and rerun the affected checks. These SHAs identify an
acceptance tuple, not permanent restrictions on upstream development.

Observed readiness:

- GitHub authentication works. The maintainer can push to the ABACUS personal
  fork and ATST; ABACUS upstream changes go through a fork PR into `develop`.
- The original ABACUS checkout has unrelated local changes. Preserve it and
  reuse the clean review worktree. Create separate ATST worktree isolation;
  do not advance its parent application's submodule pointer as a side effect.
- Current ABACUS CI builds its PR's engine, installs `interfaces/ASE_interface`,
  runs embedded unit tests, then the SCF/relax/MD/band/magnetic scripts. Some
  scripts only exercise execution or artifact existence. Socket has no entry
  in that integration launcher. Numerical handoff coverage needs strengthening.
- ATST's calculator adapter prefers an installed plugin, but `utils/io.py`,
  `utils/reverse_config.py` and `utils/gate_compensation.py` directly import
  vendored I/O. `workflows/md.py` independently falls back on broad
  `ImportError`. Several parser tests explicitly import vendored modules.
- An existing downstream caller outside this task,
  `app-tools-forge/toolbox/ABACUS/utils/abacus_structure_io.py`, directly imports
  ATST's vendored `generalio`. Preserve that import path until its owner
  migrates it or a tested compatibility forwarder supports it. This task does
  not authorize a Paimon migration or parent submodule-pointer update.
- With installed ATST 2.2.8 and independent abacuslite on Python 3.12 / ASE
  3.29, the five existing interface suites passed **70 tests**; factory,
  reverse configuration, gate compensation, MD and constant-potential suites
  passed **85 tests with 1 skip** (the optional toolbox equivalence test lacks
  its toolbox utility in this environment). These are mixed external/vendored preflight
  results, not proof that the independent path is complete.
- A local ABACUS build exists, but its recorded source is `94576a801` from
  September; it cannot establish latest-develop acceptance. Build the current
  selected revision using existing ABACUS toolchain/CI assets.
- SAI SSH and Slurm are reachable; `4V100` was UP at inspection. Verify the
  actual module/binary identity, account, quota and allocation before running.
  Available module labels include develop `079fd0c` from July, LTS 3.10.1 and
  3.11.0-beta9; none has yet been established as the current `4b92455ca` build.
  No engine calculation or scheduler job was submitted during this preflight.

Local raw preflight logs are retained at
`~/scratch/abacuslite-atst-latest-preflight.log` and
`~/scratch/abacuslite-atst-workflows-preflight.log`.

## Integration decisions

1. Use the same independently built candidate wheel across the two consumers.
   Before publication, CI builds it from a reviewed commit; do not require a
   nonexistent PyPI version or consume an unrecorded moving branch. Record
   the engine source/binary, plugin source/wheel, ATST source/wheel, dependency
   versions and numerical inputs with each result.
2. ABACUS owns engine tests, assets, numerical references and failure artifacts.
   abacuslite owns the parser/calculator implementation and its unit tests.
   Any ABACUS-side compatibility helper only adapts installation/configuration
   and test entry points; it must not become another parser implementation or
   a same-named package that shadows the installed plugin.
3. First establish an external-package candidate lane alongside the existing
   path. Use separate environments/directories for baseline and candidate.
   Remove duplicated runtime implementations only after all callers migrate,
   the independent release is installable, and compatibility checks pass.
4. ATST chooses one backend centrally for calculator and I/O consumption. A
   missing top-level plugin may use the temporary fallback; an installed but
   broken plugin must fail visibly. Workflow and launcher policy stays in ATST.
5. Candidate integration, production dependency cutover and upstream merge are
   separate recorded outcomes. A passing fork branch or opened PR is not an
   upstream merge. Define technical acceptance and production migration
   separately below; report external review/release dependencies explicitly.

## Task 1: ABACUS candidate-package integration

- [x] Branch from refreshed upstream `develop` in an isolated checkout.
- [x] Adapt `.github/workflows/ase_plugin_test.yml` to install a candidate
  wheel in a separate job/environment, retaining the existing engine build
  recipe and failure-directory upload. Support an explicit reviewed plugin
  ref for coordinated candidate runs. Ordinary PRs test their own engine;
  scheduled runs may detect drift against plugin main.
- [x] Execute from outside the bundled package directory. Check installed
  distribution metadata and `abacuslite.__file__`; also record the executable's
  `--version` and engine source revision. Deliberately test that a local source
  shadow or wrong installed distribution fails the external lane.
- [x] Reuse `interfaces/ASE_interface/tests/{scf,relax,md,band,magnetic}.py`
  and `common.py`. Make command/asset configuration explicit where needed.
  Preserve existing references and failure artifacts; keep plugin-owned unit
  regressions in the plugin CI rather than invoking old source modules and
  claiming that they exercise the installed wheel.
- [x] Strengthen observable assertions: SCF energy/forces/stress and available
  Fermi level, atom order, finite MD frames, relaxation force handoff, band
  dimensions/values and magnetic moment ordering. Use existing independently
  justified references or engine-owned raw facts with explicit units and
  tolerances. Baseline/candidate equality alone is not a scientific oracle.
- [x] Add a bounded real socket case: fixed cell, multiple position updates,
  requested properties and process shutdown. Set a timeout and retain failure
  output. Verify capability from this built engine rather than assuming it.
- [x] Run the latest engine against both bundled baseline and independent
  candidate using equivalent inputs. Attribute failures to baseline engine,
  plugin, harness or environment; do not loosen references to obtain green CI.
- [x] Update `interfaces/ASE_interface/README.md` and
  `docs/advanced/interface/ase.md` with the actual candidate installation and
  test route; complete independent review and upstream governance checks.
- [ ] Deliver the reviewed PR to `deepmodeling/abacus-develop:develop` and
  inspect actual remote CI results after the local validation checkpoint.

Acceptance: the current engine and installed independent package complete the
engine-owned suite with explicit numeric/property checks, import provenance,
socket evidence and preserved logs. Mark upstream review/merge separately.

## Task 2: ATST external-backend integration

Start implementation and local checks independently when useful; the final
real-engine acceptance follows Task 1's engine/plugin qualification.

- [x] Branch from refreshed ATST `main`, preserving the parent checkout.
- [x] Route the remaining direct imports and MD fallback through the existing
  backend decision in `calculators/abacuslite_backend.py`. Cover INPUT/STRU,
  K-point helpers and legacy/latest readers as used by `utils/abacus_io.py`,
  `utils/io.py`, `utils/reverse_config.py`, `utils/gate_compensation.py` and
  `workflows/md.py`. Preserve supported public API, CLI and YAML semantics.
- [x] Add an installed external-backend job to ATST's own PR CI, independent of
  vendored snapshot maintenance. Build/install this PR's ATST wheel with the
  candidate plugin wheel. Run consumer checks outside the source checkout and
  assert `BACKEND_SOURCE == 'external'` and both installed import locations.
- [x] Exercise actual public consumer paths while rejecting vendored imports
  in the external-path tests. Check structure/force ordering, Fermi retention,
  profile version/launcher policy, restart/frame selection, MD reading,
  reverse-config generation and constant-potential handoff. Keep explicit
  fallback tests in a separate environment without the plugin. Include a
  broken-installed-plugin case that must fail rather than silently fall back.
- [x] Run relevant existing suites, the ordinary offline suite, package build,
  dependency checks and `scripts/verify_wheel_api.py`. Parser unit tests that
  explicitly target the snapshot remain labeled transition evidence.
- [x] Run affected ABACUS workflows on trusted SAI compute allocations under
  the repository's maintenance rules (`4V100`, LCAO `ks_solver: cusolver`).
  Reuse curated cases: relaxation, short MD/restart, a serial NEB and an
  image-parallel NEB/AutoNEB case, plus a bounded constant-potential case that
  exercises Fermi/result handoff. Record whether each run establishes a
  handoff smoke or convergence against an existing scientific reference.
- [x] Use the qualified latest-develop engine for the primary tuple; retain
  LTS 3.10.1 as a separately identified compatibility check for the legacy
  reader and existing ATST references. Prepare a matching current-develop
  GPU build if the site only provides an older engine. Never relabel an LTS
  run as develop acceptance. Recheck site account/storage/MPI before submission;
  ordinary community PR CI must not submit cluster jobs or receive credentials.
- [x] Update README, developer backend-maintenance guidance and the required
  documentation/status ledgers. Run `scripts/check_docs_governance.py`, obtain
  independent review and retain the candidate branch.
- [ ] Deliver its PR and verify remote CI after the local validation checkpoint.

Acceptance: no mixed implementation is used by the external consumer path;
installed-wheel, offline behavior and the selected real workflows pass, with
their engine/plugin/consumer tuple and validation scope recorded.

## Task 3: Release, dependency cutover and completion

- [x] Reconcile any fixes discovered in either consumer into the owning repo,
  then rerun both acceptance tuples with the final plugin artifact. Do not
  release a wheel different from the one validated without revalidation.
- [ ] Prepare the plugin release, exact artifacts, release notes and retained
  evidence. Request release authorization only when this concrete result is
  ready; publish and verify a fresh indexed installation after authorization.
- [ ] Switch ABACUS CI from the candidate source reference to the tested
  indexed package; preserve an explicit candidate override. Switch ATST's
  declared dependency to the validated compatible release range, and test the
  minimum plus current supported package versions. No unpublished dependency
  is added to a production release.
- [ ] Retire the old implementations after the caller inventory is clean. Keep
  necessary compatibility entry points thin. ATST internal acceptance alone
  does not authorize removing the known Paimon import path; test its forwarding
  behavior without expanding this task into Paimon runtime changes. If the old ABACUS
  `pip install interfaces/ASE_interface` entry is retained, use a distinctly
  named dependency-only distribution; it must neither depend on itself under
  the `abacuslite` name nor ship a shadowing `abacuslite` package. Confirm this
  legacy-install contract with upstream before that removal/cutover PR.
- [ ] Land ATST changes and obtain the ABACUS upstream integration outcome.
  Required-check activation needs the corresponding repository maintainer;
  distinguish visible successful CI from enforced merge blocking.
- [ ] Record final accepted revisions, CI links, engine outputs, ATST workflow
  evidence, indexed-install result and remaining upstream disposition.

## Completion boundaries

**Technical acceptance** means Tasks 1 and 2 pass with the same final candidate
plugin, reviewed consumer changes, persistent CI and reproducible real-engine
evidence. Deliver the two mergeable PRs and record their status. Missing engine
or workflow evidence keeps technical acceptance incomplete.

**Production migration** additionally requires Task 3: an authorized indexed
release, production dependency cutover, compatibility-path handling and the
actual repository merge outcomes. Pending upstream review must remain visible
as pending; it is not an implementation test failure.

The maintainer confirmed the technical-acceptance gate: both candidate code
changes, CI and real runs must pass and mergeable PRs must be delivered before
returning to Forge. Publication and community merges remain separately tracked.
The subsequent instruction explicitly requires completing local validation first;
do not create PRs while local or trusted SAI acceptance is incomplete.

## Completion checklist

| Milestone | Evidence needed | Current state |
| --- | --- | --- |
| Latest branches and candidate identity | Fetched SHAs, installed import paths | Verified |
| ABACUS independent-package lane | Actual current-engine run and numeric handoff checks | Final local pass: 9 bundled + 9 external; remote CI pending |
| ATST unified external path | No-vendored consumer tests and wheel checks | Final offline/wheel checks pass |
| ATST affected workflows | Current-engine and separately scoped LTS run records | Local/trusted GPU acceptance passed; see scoped evidence reuse below |
| Indexed distribution and production cutover | Authorized release, fresh install, consumer dependency checks | Pending |
| Repository integration | Reviewed/merged changes or explicit upstream disposition | Pending |
| Forge continuation | Both consumers technically accepted and mergeable PRs delivered | Deferred; local acceptance first |

## Execution evidence (in progress)

- ABACUS candidate `68d23825a`: installed bundled 1.0.0 and external 1.1.0rc1
  each pass all eight real engine-owned cases on freshly compiled `4b92455ca`
  CPU MPI/LCAO. Source tests run in separate processes as in `xtest.sh`.
  The external wheel is `b5001daeefe3f084648360974a38599c318423cdcbed794de082b56d64906738`.
  Both lanes retain eleven raw engine logs plus INPUT/STRU/KPT and outputs in
  `~/scratch/abacuslite-engine-final-68d2382/`; `evidence.json` binds the tuple.
- ABACUS review corrections: band values use raw eig_occ rows, AFM moments
  compare in atom order, socket shutdown is bounded. Real execution found the
  socket harness's default `all_changes` argument invalid on its second frame;
  it now passes ASE `check_state`. Both socket paths pass two updates and zero
  client exit. These are harness corrections; the plugin runtime did not change.
- ATST `df4c471`: no-plugin offline suite 1194 passed / 32 skipped;
  installed-wheel Python 3.12 consumer suite 52 passed / 2 skipped.
  The initial Python 3.13 consumer run also passed 52 / 2; the subsequent guard
  correction passed its focused 3 / 1 check on Python 3.13. A temporary copy
  restoring the old top-level vendored import correctly fails the new fresh
  subprocess guard. Independent review accepted both consumer changes.
- ATST wheel `2bf8a5e6c9d1d3f8b306817ebba97d01cba701e8d268daab59c59e178ffd50a5`
  was built from `07e0350`; all 103 wheel Python files match `df4c471` (the latter
  changes only tests/docs). All eight plugin Python files match `136783b`.
- Build ruling: the scoped PBE interface cases do not exercise optional JSON,
  DFT-D4 or LibXC. The local existing DFT-D4 installation is older than current
  develop requires; JSON/DFT-D4/LibXC are disabled for this acceptance build,
  not represented as validated features. GPU build also disables ELPA/LibRI.
- SAI build job 1819688 completed on 4V100 with source `4b92455ca`, CUDA 12.9,
  sm70 and Open MPI 5.0.10. The retained `abacus_basic_gpu` SHA-256 is
  `409dd40fc66e5ce4f71025bf979ddc4201c4147419b5839e314b362a346875e5`.
  It reports v3.11.0-beta10; the beta9 site module only supplies its dependencies.
  Runtime job 1819838 uses this exact binary and both installed wheels in a
  temporary venv, with 4V100 GPUs and cusolver. `pip check` passes. Real workflow
  acceptance remains pending. Job 1819830 was cancelled while queued to correct
  the runtime driver before execution.
- SAI storage ruling: both user persistent locations exceed file quotas.
  Builds/runs use compute-node `/tmp`; the controller streams retained archives
  into local scratch. Existing site environments and persistent files are not
  modified. The temporary venv updates Sella 2.4.2 to the declared supported
  2.6.0, while retaining the site's MPI-compatible mpi4py.
- No PR, PyPI publication, production dependency cutover or Forge change has
  occurred. Local validation must finish before PR delivery.

### Real-run findings and final candidate rerun

The initial successful eight-case ABACUS tuple above predates the native-MD
fixes below. It must not be presented as final acceptance of the new tuple.
Both authoritative remote heads were fetched again after these fixes and
remain `4b92455ca` (ABACUS develop) and `45d8c78` (ATST main).

- SAI job 1819838 ran relaxation successfully, then the acceptance harness
  passed a string to the reader's Path interface. The retained post-hoc raw
  check passes; the original job remains failed. The harness now passes Path.
- SAI job 1819893 passed relaxation, ASE MD/restart, serial NEB and the separate
  LTS relaxation. Native MD returned engine exit zero but ATST searched the
  run root instead of `OUT.<suffix>`, yielding no trajectory. The Pt baseline
  completed, but compensation expected legacy `SPIN1_CHG.cube` while current
  develop writes `chg.cube`. These are real consumer defects, not engine or
  scientific-convergence failures. Its dependent CP check did not run.
- Native-MD investigation also exposed an inherited parser defect: MD_dump's
  lattice vectors are dimensionless and must be multiplied by its Angstrom
  lattice constant. Independent abacuslite `dc020430bfa8c76edfc275b0f1eab2f12cc29d4d`
  fixes only the native-MD Atoms construction and sets periodic boundaries.
  The low-level dump dictionary contract stays unchanged. Source and installed
  wheel tests pass (113 passed / 15 skipped); independent review accepted it.
- Ruling: ATST owns output-directory selection and the failure state when an
  engine exits zero without readable frames; abacuslite owns parser units.
  Preserve flat historical outputs only when the exact configured output
  directory is absent, and never combine files from different directories.
  The vendored fallback receives the same narrowly registered parser patch.
- Ruling: accept complete current or LTS density-file naming families, reject
  ambiguous/mixed/incomplete spin files and indexed output, and preserve all
  existing numerical, geometry and electron-count validation.
- ATST `2e599081fc2a6fb10e6059b6a4769ace1e7caa54` implements those repairs.
  No-plugin Python 3.13 suite: **1211 passed / 32 skipped**;
  isolated installed ATST + plugin Python 3.12 consumer checks:
  **63 passed / 2 skipped**. Raw logs are
  `/tmp/atst-final-offline-fallback.log` and
  `/tmp/atst-final-external-installed.log`. Snapshot drift, documented-patch
  mutation, documentation governance and clean installed-wheel API checks pass.
- ABACUS `bca816410dcd8e380f2d84306c3e317e9d3b0716` applies the same native-MD
  parser repair to its bundled comparison path, adds a real native-MD case
  with raw cell/position/force checks, and pins the independent candidate to
  `dc02043`. Both final CPU lanes passed all nine real cases, including native
  MD and socket. All script exit codes are zero; raw outputs and provenance
  are retained in `~/scratch/abacuslite-engine-final-bca8164/evidence.json`
  (SHA-256 `8a2069c5a88a03c0612ecaa29b3a0a481eaeaa40f3b4c229293f4b917d710a17`).
- Parallel NEB completed in job 1819893, but the harness incorrectly required
  every optional API profile on rank zero to be populated. Existing API
  profiles are best-effort for rank-owned images. The corrected acceptance
  uses the globally gathered persisted final band, requires finite energy and
  forces for every image, and matches each image to literal engine output.
  Available API profiles must still match that band. This changes the harness,
  not workflow result semantics or numerical tolerances.

Final candidate artifact identities (both consumers must validate this plugin):

| Artifact | SHA-256 |
| --- | --- |
| abacuslite 1.1.0rc1 from `dc02043` | `c809d0714c36ee52358e5a102912d979c0a1b82ad4a5b97811582a62066e27fd` |
| ATST 2.2.8 from `53d6b7c` | `4008ca72bcacbd0393d8c154eaf1cbbc80d320e1b64178cb8588fbfd072c5e40` |

The controller compared every shipped Python file to its frozen source (8 in
abacuslite, 103 in ATST). The runtime harness additionally compares installed
files to the wheel and rejects any vendored import. The subsequent final
runtime result is recorded below; neither artifact has been published.

The final plugin's wheel/sdist and sdist-rebuilt wheel all pass strict metadata
validation. An isolated installation of the rebuilt wheel passes **113 tests /
15 skips** outside the checkout, and dependency checks pass. The source,
sdist, direct wheel, rebuilt wheel and CPU-accepted wheel have identical package
Python files; all uncompressed members of the three wheels match. Archive
timestamps change whole-wheel hashes without changing payload. Packaging
commands, raw logs and member comparison are retained in
`~/scratch/abacuslite-dc02043-package-final/`; the sdist SHA-256 is
`51236399e6dfcea48f9bc9f1519499a3421a118f92abdca111d403e4445e4a32`.
The final real runs continue to use the original `c809d071…` wheel unchanged.

Independent review of both final consumer changes and the frozen runtime
harness found no blocking issues. SAI job **1820042** runs the final tuple on
4V100 with the exact current-develop GPU binary. The historical failed job
1819893 archive is retained locally, SHA-256
`1685a398a70097efd2d2ff561c6aa386dd2d3ddb36363fcf46a62473e3895f83`.
Post-hoc checks with the repaired code confirm its two native MD frames have
the correct 10 Angstrom cell, its density integrates to 217 electrons within
the existing tolerance, and all four persisted images in each NEB match raw
energy/force output. Those post-hoc checks explain the repairs; they do not
change the original job's failed status or replace the final rerun.

Job 1820042 subsequently completed: eight cases passed, including native MD,
the Pt fixed-electron baseline, image-parallel NEB and LTS 3.10.1. Its CP case
failed because ATST recognized only the legacy SCF convergence wording. The
current engine's raw log explicitly contains `#SCF IS CONVERGED#`; this is
also the success branch in engine `source/source_io/module_output/output_log.cpp`.
ATST must recognize that exact marker and `!!SCF IS NOT CONVERGED!!` while
preserving old regexes, failure precedence and rejection of missing evidence.
The archive remains a failed run (exit 1), SHA-256
`5370d7afeee38d27eab282bda15a1f8310fd6f452ece6e1ee7cbbe9d5f78a4bd`.

Ruling: fix the bounded CP convergence reader in ATST, then rerun real CP and
image-parallel NEB with explicit process exit records. Reuse the independently
passed fixed-electron baseline only after verifying its evidence hash, engine,
plugin and all input asset hashes. The baseline workflow and plugin do not
change in this repair. Reuse unaffected passed cases only after checking the
new wheel differs in the CP reader alone. Preserve the site's MPI shutdown
warnings in raw output; do not silently filter them or infer a process exit
from a root-rank success message.

### Local acceptance checkpoint

ATST `53d6b7c50c17cb536ea464ec0335ee1e69c206cd` implements the additive SCF
marker repair. Independent review found no blockers. Its full offline suite
passes **1223 tests / 32 skips**, and the installed-wheel CP suite passes
**54 tests**. The earlier 63 / 2 installed consumer suite remains valid for
the unchanged consumer paths. Wheel comparison verifies that among all 103
production Python files the sole difference from `2e59908` is
`atst_tools/calculators/constant_potential.py`. All new wheel Python files
match the frozen `53d6b7c` source.

SAI job **1820187** reran CP and two-rank image-parallel NEB with that wheel,
the unchanged `dc02043` plugin wheel and the identical `4b92455ca` GPU binary.
Both cases pass; the CP batch and outer MPI launcher each return **0**, and
the overall job exits **0**. CP's chemical-potential residual is **0.0 eV**
against the same-engine fixed-electron baseline; raw energy/force and grand
potential bookkeeping checks pass. Baseline reuse verifies the evidence and
raw-log hashes, engine binary hash, plugin wheel hash and every input asset
hash. This is a bounded handoff check, not a root-finding or scientific
convergence benchmark. MPI emits site UCX shutdown warnings; these remain in
the raw log, and the verified outer MPI exit code is zero.

| Runtime acceptance scope | Executed evidence |
| --- | --- |
| Relax, ASE MD and restart, native MD, serial NEB, fixed-electron Pt baseline | Passed job 1820042 with `2e59908`; these paths are unchanged in `53d6b7c` |
| CP and image-parallel NEB | Passed job 1820187 with final `53d6b7c`; explicit process exit records |
| LTS 3.10.1 legacy reader | Separate passed compatibility case in job 1820042, not labeled develop evidence |

The aggregate local manifest is
`~/scratch/abacuslite-integration-acceptance-final.json`; it records each case's
actual source/job rather than pretending all cases ran in one successful job.
It binds 99 raw file hashes, both wheel comparison maps, dependencies,
provenance and the baseline reuse checks. Raw archives and scripts are retained
under `~/scratch/abacuslite-sai-final-1820042/` and
`~/scratch/abacuslite-sai-cp-rerun-1820187/`. The final rerun archive SHA-256 is
`b1803ced6d92c856634b0119dfb8775cc355d6fa617c858307c93c9430e4b373`.
CPU evidence remains `~/scratch/abacuslite-engine-final-bca8164/evidence.json`
with **9 bundled + 9 external** cases passed.

The selected local phase is complete. No PR/push, indexed publication,
production dependency cutover or Forge change has occurred. Remote CI and PR
delivery remain the next integration phase before the agreed return to Forge.


## ATST 2.2.9 paired-installation follow-up (2026-10-17)

Workflow: L3, continuing the approved integration plan. The maintainer asked
for dedicated environments proving installed abacuslite behaves at least as
well as vendored ATST, plus candidate-sensitive upstream/downstream CI in both
repositories. Local validation precedes PR delivery; no push, publication or
Forge change is part of this follow-up.

Ruling: refresh ATST to current `origin/main` `1081b9d1fed06842ee1d95dfbeb542ed81c57d49`
(version 2.2.9) before acceptance — prior 2.2.8 evidence does not cover new
scientific contracts — ignoring the update could conceal a consumer regression.
ATST integration merge `a56732c` retains the local backend/MD/CP fixes. The
independent plugin receives the new default SCF identity tolerance `1e-5 Å`;
its boundary regression fails on the previous default (4 failed, 2 passed).
The unrelated dirty `atst229-alignment` worktree is preserved untouched.

Acceptance sequence:

- [x] Build wheels, create two clean Python environments with identical
  dependencies and the same ATST wheel; install abacuslite only in the external
  lane using pip. Record wheel/source identities, package locations, dependency
  sets, full offline results and skip reasons.
- [x] Exercise actual consumer paths in fresh processes, prevent silent backend
  mixing and compare numeric fixtures against independent expectations. Keep
  explicit vendored maintenance tests distinguishable from consumer coverage.
- [x] Run paired real GPU cases with the same engine/inputs, independently check
  raw outputs, record state/artifact differences and precise numerical bounds.
  This establishes interface handoff, not scientific convergence for every
  transition-state algorithm or optional unrelated calculator backend.
- [x] Both repositories test their own candidate wheel against the counterpart;
  reuse one ATST-owned installed-consumer runner, retain pinned acceptance plus
  scheduled/main and manual coordinated-reference checks. Demonstrate meaningful
  mutations fail, and distinguish committed configuration from activated remote CI.
- [x] Independently review the final changes/evidence and document any remaining
  coverage limits before reporting this follow-up complete.

Raw local evidence: `~/scratch/abacuslite-atst229-parity/`; paired real-runtime
harness/results: `~/scratch/abacuslite-atst229-paired-runtime/`.


### Paired installed-wheel evidence

The accepted ATST code/test revision is `87caeedbca5ed7104316bfc6130fd2598b6c5e4b`;
its production Python files exactly match the `a56732c` wheel. Plugin CI configuration
is recorded at `c2fc8f1f209fa3f055f14ad5fdfdbff45ea5bffa`; production files match
`06f97b1bda59f3d29e93dd5c7a4bf598808b89b8`. The latter applies the ATST 2.2.9
SCF identity tolerance. Plugin installed unit tests pass 119 / 4 skips.

| Installed comparison | Vendored | External plugin | Comparison |
| --- | --- | --- | --- |
| Python 3.12.3, ASE 3.29.0 | 1390 passed / 38 skipped | 1392 passed / 36 skipped | Passed |
| Python 3.12.3, ASE 3.28.0 | 1390 passed / 38 skipped | 1392 passed / 36 skipped | Passed |

Each lane collects the same 1428 test identities. In each pair, all 33 other
installed distributions are identical; only external adds abacuslite. Numeric
facts match independent fixture constants. Both startup and finish of the
pytest process attest installed package paths. A separate fresh process guards
actual consumers against vendored imports. Full-suite tests that read relative
document/example paths run at the ATST root with installed wheel imports;
consumer probes and plugin-owned contracts execute outside source checkouts.
Explicit vendored maintenance tests are retained and are not represented as
external-backend coverage. Backend-specific tests explain the outcome
variation; optional DeePMD models, scheduler cases, missing toolbox reference
and source/distribution-specific tests remain visibly skipped.

Both environments pip-install the same ATST wheel (SHA-256
`bffbc2d3ada4f3ee7cfb9ba6f1b7e36bf6ca98171dac9a61854ed7c02bb59059`).
Only external pip-installs abacuslite (SHA-256
`4715299fe25b4ff583b577a4024d45eb2f338cd2aa2bb1d3c2db5066588abac9`).
`wheels.json` binds every production Python file to its frozen source; both
wheels and the plugin sdist pass strict Twine checks. The optional ATST wheel
inspection also passes when supplied `ATST_DIST_WHEEL`; no new ATST sdist
release is claimed by this follow-up.

The installed comparison at `probe_improvements.py` establishes two concrete
improvements over this vendored baseline: mixed legacy/latest calculators
work in both creation orders, and high-level `read_abacus_out` supports repeated
reads without deleting `eig_occ.txt`. Vendored fails those three probes;
external passes. The lower-level `read_band_from_eig_occ` alone is read-only
in both implementations and is not used to claim an improvement.

The plugin-owned installed ATST/Forge contracts pass 10 tests. Independent
mutations of installed copies show that removing MD cell scaling, reverting
instance-specific reader choice, and restoring high-level eig_occ deletion
all fail their behavior tests. Restored files reproduce 10 passed. An ATST
consumer deliberately routed back to vendored is rejected by the fresh-process
guard. Source trees and the paired environments are untouched by mutations.

### Candidate CI and review

ATST changes test their current wheel against plugin `06f97b1`; plugin changes
test their current wheel against ATST `87caeedb` and Forge `43f5d4a`. Both use
the ATST-owned installed-consumer runner. Scheduled jobs follow counterpart
main heads; manual refs support coordinated changes. Dependencies, wheel/file
identities, test identities/outcomes and numeric facts are compared, not merely
a final pytest exit message. No release or cross-repository write token is used.

Independent review found and closed a real failure-propagation defect:
plugin consumer `pytest | tee` previously returned 0 when pytest failed.
The corrected explicit Bash/pipefail step returns 1 for the same intentionally
wrong SCF energy expectation (1 failed / 9 passed); restoring the test returns
0 with 10 passed. Exact command/log/JUnit evidence is retained under
`~/scratch/abacuslite-consumer-contract-229/ci-pipefail/`. Review also corrected
documentation that had mixed the historical GPU tuple with the new candidate.

Read-only GitHub settings inspection confirms plugin main has no protection or
ruleset. ATST main has no required status checks; its existing named ruleset
only protects `v1.5.0` from deletion/non-fast-forward. Thus these locally
implemented checks are not yet enforced merge gates. After local acceptance,
the activation dependency is: make plugin `06f97b1` fetchable, make ATST
`87caeedb` fetchable, then validate the plugin CI commit. Only after remote
checks actually pass should main require `compatibility-gate` (plugin) and
`paired installed abacuslite consumer parity` (ATST). PR delivery, remote CI,
required-check configuration and indexed publication remain separately tracked.

The full offline evidence index is `~/scratch/abacuslite-atst229-parity/evidence.json`.
Raw logs retain upstream warnings; no blanket warning filter was introduced.
The completed paired real-runtime result is recorded separately below.


The final installed suite also covers Python subprocesses. An additional audit
found source-tree `PYTHONPATH` injections in runtime/plot/CLI tests, invisible
to parent pytest attestation. `87caeedb` introduces an installed-test mode,
shared subprocess-environment helper and lazy origin guard. Actual child imports
resolve inside the environment; deliberate source shadowing exits nonzero.
The guard uses `find_spec` without preloading NumPy/ASE, preserving lazy import
and short-worker timeout behavior. The earlier eager guard's failures are kept
as harness-development evidence. Both ASE versions were then rerun in full
with the final guard (the 1428-case results above); no production code changed.

### Paired real-runtime checkpoint

SAI job `1827672` completed with `0:0` in 20:34 on `4v100n15` with two V100s.
The same frozen ATST wheel and ABACUS binary ran in two isolated Python 3.10
venvs with the same site dependencies; only the external lane installed the
plugin. Import guards, every installed Python file, `pip check`, dependency
sets and identical asset hashes were verified before comparing results.
Both lanes passed all ten cases: Relax, ASE MD initial/restart, native MD,
serial/two-rank NEB, Pt fixed-electron baseline/constant-potential handoff,
finite-difference vibration and a separately identified LTS 3.10.1 run.
All twenty recorded stages and the outer streamed process returned zero.

The independent comparison uses tolerances fixed before reading external
results: energy/EF/mu/Omega `1e-5 eV`, forces `1e-4 eV/Å`, positions/cells
`1e-8 Å`, frequencies `1e-3 cm^-1`; the finite-difference Hessian uses
`1e-2 eV/Å²`, accounting for two force errors over the `0.02 Å` span.
All selected cross-lane values are identical at stored precision. The additional
154-check artifact audit reads every MD/NEB trajectory frame, native MD_dump
frames and literal raw energies, all seven vibration force caches and their
central-difference Hessian. Maximum raw-vs-trajectory discrepancies are
`2.0e-10 eV` and `5.7e-8 eV/Å`. These raw rounding differences are distinct
from the zero cross-lane differences. The manifest hashes 599 archived lane
files, including inputs, outputs and harness/provenance files.

The external high-level reader reads eleven relax/CP/NEB outputs twice with
unchanged raw log/eig_occ/STRU hashes. Vendored removes eig_occ after reading;
external preserves it. Artifact roles and numerical handoff remain equivalent.
The GPU engine is the selected `4b92455ca` / v3.11.0-beta10 binary (SHA-256
`409dd40fc66e5ce4f71025bf979ddc4201c4147419b5839e314b362a346875e5`).
The LTS compatibility case has its own recorded v3.10.1 binary hash and is not
misrepresented as develop engine evidence.

Full report and raw artifacts:
`~/scratch/abacuslite-atst229-paired-runtime/attempt3-corrected-gpu/REPORT.md`.
The successful archive SHA-256 is
`930b4f7a94f9372345dba4b31ea725211f0048ba584abdea0fea635998e70e40`.
`comparison.json`, `artifact-audit.json` and the frozen analysis scripts retain
all thresholds, differences and file identities. Earlier queued/cancelled GPU
attempts and the partial CPU preflight remain separate; none is counted as a
completed paired acceptance.

Scope: the full offline suite covers the wider ATST API/workflow contracts,
including transition-state paths. The ten real cases validate interface and
data handoff, not optimizer/scientific convergence. Single-step Relax/NEB
retain their nonconvergence warnings. H2 vibration has two imaginary modes;
it tests finite-difference plumbing, not a valid transition state. Dimer,
Sella TS, CCQN and IRC have no new real-engine runs in this follow-up. Vibration
cache stores forces only; per-displacement energies are not independently
claimed. No assertion of universal compatibility across arbitrary future
engine versions or untested scientific inputs follows from these results.

Independent final review passed with no remaining blockers. The reviewer checked
the final subprocess guards, both ASE comparisons, production-file identities,
the successful archive and all 599 archived lane hashes, and independently
recomputed the 110 trajectory/native-MD/vibration numeric checks. The other
44 artifact checks cover the bounded repeat-read behavior described above.
This completes the local acceptance checkpoint within the documented scope.
No candidate push, PR, indexed publication, production dependency cutover or
Forge modification has occurred in this follow-up. `pip install` here means
installing the recorded candidate wheels; ATST does not yet pull a published
abacuslite version automatically from PyPI.


## Develop/LTS compatibility audit (2026-10-17)

The maintainer requested the same installed-package and CI assessment for both
ABACUS branches, and explicitly confirmed that LTS compatibility must be
provided through `legacyio` although LTS does not carry the new interface.
This follow-up investigates that requirement; it does not authorize a release,
PR delivery or changes to upstream branch protection.

Ruling: treat LTS as a supported external engine target, not as a vendored
comparison lane. Test automatic per-instance legacy-reader selection and real
input/output handoff. Do not backport the whole develop interface or require
its newer output files/socket protocol just to obtain a symmetric matrix.
The cost of a mistaken format assumption is a false acceptance or an avoidable
LTS regression, so raw output and the engine source identity remain explicit.

- Refreshed develop: `73cd094361f77574f9b28e825913e00f1d2c742a`, two engine
  commits after the previously tested `4b92455ca`.
- Refreshed LTS: `725bf475a7159db4c1890a1f55160393e14b6b13`; no `interfaces/`
  tree or ASE-plugin workflow. Its documented historical interface is
  `ase-abacus`, which is distinct from this independent distribution.
- Initial plugin baseline: the installed `06f97b1` production wheel, SHA-256
  `4715299fe25b4ff583b577a4024d45eb2f338cd2aa2bb1d3c2db5066588abac9`.
- The focused installed-wheel legacy/reader/instance contract tests pass
  **25 tests** from outside the checkout. Raw output:
  `~/scratch/abacuslite-engine-branches-audit-20261017/legacy-installed-offline.log`.
  This result alone does not establish current-engine compatibility.
- Upstream develop's existing ASE workflow has recent successful runs but
  tests its bundled plugin. Our independent-package workflow remains local at
  `bca8164`, with historical default plugin pin `dc02043`. The plugin-owned
  workflow currently has no `--run-engine` job for either engine line.
- Read-only remote observations are retained in the same audit directory as
  `remote.json` and `develop-effective-rules.json`. Develop is reported
  protected, but visible effective rules only block deletion/non-fast-forward;
  its branch-protection details endpoint returns 404 to this account. LTS is
  reported unprotected. No claim of an enforced abacuslite merge gate follows.

Both refreshed engines were built locally from exact `git archive` sources in
`~/scratch/abacuslite-current-branches-20261017/`, without modifying the
integration checkouts or replacing earlier binaries. Develop executable SHA-256
is `ae341d54d3ddfe84061c5d29266a732bdc146b8a7bf983c477ca900c929e9e19`;
LTS executable SHA-256 is
`72cc354b0dc3b80479525923a880d39f2b423eef093e4ae27126175cf64a8b63`.
These are bounded CPU/MPI/LCAO interface builds, not full-feature or scientific
validation of either engine. Build logs and CMake caches retain the feature
selection. LTS initially used the modern ELPA option and failed configuration;
the successful retry uses its actual `USE_ELPA=OFF` option. A diagnostic note
retains that first failure; its complete first configure log was not retained.

### Real-runtime failures and compatibility repairs

The original wheel passed develop's nine tests, but its native-MD input had
zero velocities and a static trajectory. On LTS, seven tests passed and native
MD failed: `init_vel=1` with zero temperature produced invalid velocities when
the engine rescaled to the requested temperature. Supplying nonzero ASE
velocities still wrote zeros to STRU. A separate seeded engine-generated
velocity run completed three physical frames, then exposed the reader error
`Inconsistent length: 1 != 3`. All failures and raw outputs remain in
`BASELINE.md` and its linked evidence, separate from successful reruns.

Minimal repairs are recorded in `546d706` and `ba65f606`:

- Preserve supplied ASE velocities when writing STRU, converted to atomic
  velocity units and reordered with the species. No-momenta inputs retain
  their existing zero default.
- For legacy native MD, use the existing dump parser to obtain every physical
  frame; keep Cartesian positions in Angstrom, scale lattice vectors once,
  and retain PBC. Accept the LTS `ION=2`/`ELEC=1` header spelling.
- Preserve complete historical log-only MD. Independent review caught an
  intermediate unconditional-dump requirement; the follow-up restores the
  old consumer fixtures and this API. Existing corrupt dumps cannot silently
  fall back, and incomplete log-only frame sets fail explicitly.

The real LTS log/dump fixture is retained byte-for-byte with hashes in
`tests/fixtures/lts_native_md/README.md`. Unit regressions cover physical
geometry, frame count, energies/forces, read-only output, velocity units and
species order, plus the old log-only path. Independent review of `ba65f606`
closed the intermediate compatibility finding with no remaining code blocker.
No public module layout or calculator API was replaced.

The final candidate wheel has SHA-256
`3f81661fefa3583b1bd19b680db715c0f5477d1bce5afb3f4fcd7f8dfb672850`;
its sdist is `a78813693c30d80b51125a0e111636b7e0bbcbdf58336ebd4ad587d585b4dd8c`.
Both pass strict Twine metadata checks. All eight wheel production Python
files match the recorded `ba65f606` source hashes. Build provenance separately
records the uncommitted documentation included at build time; no release was
made from these artifacts. The real-run environment uses the same Python
3.10.20 and dependency freeze as the original baseline, with only the plugin
wheel changed.

### Repaired-wheel acceptance

`~/scratch/abacuslite-current-branches-20261017/FINAL_REPORT.md` records:

| Exact engine | Real interface scope | Result |
| --- | --- | --- |
| develop `73cd094` | SCF, ASE relax/MD, native MD, band, FM/AFM/noncollinear magnetic, socket | 9/9 tests; 142 retained raw files hashed |
| LTS `725bf47` | SCF, ASE relax/MD, native MD, band, FM/AFM/noncollinear magnetic | 8/8 tests; 125 retained raw files hashed |
| Same LTS, seeded generated velocities | Native MD with zero STRU velocities, `init_vel=0`, seed 1729 | 1/1 test; 16 retained raw files hashed |

All processes returned zero with no timeout. Installed-module probes select
`latestio` for develop v3.11.0-beta10 and `legacyio` for LTS v3.10.1. The LTS
source has no socket driver, so it is not assigned that newer capability.
There is no LTS bundled-plugin comparison.

The native-MD oracle now verifies STRU initial velocity units and actual motion
as well as every frame's raw energy, forces, physical cell/positions and PBC.
Its velocity tolerance is `rtol=2e-6, atol=1e-12`, covering the independently
checked `4.63e-7` relative difference in ASE/engine unit constants. Develop
emits two frames and LTS three for `md_nstep=2`, consistent with their source
loops. Maximum minimum-image displacements are respectively `0.000666386 Å`
and `0.00131604 Å`; the seeded LTS case also moves `0.00131610 Å`.
These are short Si LCAO/MPI two-rank CPU checks; they do not establish broad
scientific accuracy, GPU behavior, or all engine features.

The intermediate log-only compatibility failure was reproduced separately
from frozen archives: `lts-logonly-evidence/README.md` records identical
focused tests failing six cases at `546d706` and passing all six at `ba65f606`.
The fixed source suite passes 124 tests with 21 skips. These are new isolated
reproductions because the first source-test output was not saved to disk.

The ATST full installed suite was rerun with the repaired plugin in Python
3.12.3/ASE 3.29.0. It passes **1392 tests with 36 skips**; comparison with the
unchanged vendored **1390/38** baseline passes the existing strict comparator
over all 1428 collected cases, installed ATST file/wheel identities, dependency
versions, skip reasons and raw fixture fact projections. The unchanged ATST
wheel remains `bffbc2d3ada4f3ee7cfb9ba6f1b7e36bf6ca98171dac9a61854ed7c02bb59059`.
Reports are in `~/scratch/abacuslite-engine-branches-audit-20261017/`:
`atst-fixed-py312.json` and `atst-fixed-py312-comparison.log`.

Harness corrections are retained honestly: the first new ATST environment
used Python 3.13.13, so its 1392/36 pass could not be accepted as a paired
comparison against Python 3.12.3. The comparator rejected that mismatch;
the new same-version environment passed without changing the comparator.
The first copied plugin test tree omitted `examples/`, causing eleven missing
file failures; restoring the unchanged examples gives 124 passed/21 skipped
in `fixed-offline-complete-harness.log`. The original failed logs remain.

The final Python 3.12 installed-wheel rerun also passes **124 offline tests
with 21 skips** (`fixed-py312-offline.log`). After the paired ATST comparison,
Forge was installed from the pinned `43f5d4a` archive; `pip check` passes and
all **10 plugin-owned ATST/Forge consumer tests** pass from the copied test tree
outside checkouts (`fixed-py312-consumers.log`). Import assertions require all
three packages to resolve inside the virtual environment. No Forge production
source or dependency selection was changed by this follow-up.

Independent final review verified all **283 retained raw-file hashes**,
engine/wheel/harness identities, and byte equality of the eight plugin Python
files across commit, wheel and installed package. It independently reread all
three native-MD trajectories and checked raw energy/geometry/forces/PBC,
velocity units and actual motion. Review also confirmed the strict same-Python
ATST comparison and the isolated log-only RED/GREEN reproduction. No blocking
finding remains within this local CPU/MPI interface acceptance scope.

The next CI work remains explicit: add plugin-PR jobs using its own wheel
against pinned develop/LTS engines, add scheduled branch-head checks, and
complete the engine-side external-package lane with current plugin pin and
explicit binary identity. The current LTS absence of `interfaces/` does not
remove that legacy compatibility obligation. This audit did not add those
live-engine workflow jobs or activate required checks. No push, PR, PyPI
publication, production dependency cutover or upstream settings change was
performed.

Earlier develop `4b92455ca` paired CPU/SAI results and the previous v3.10.1 ATST
relax result remain historical evidence, not reruns with this repaired wheel.
Current CI gaps and the required two-format contract are described in
`docs/compatibility-ci.md`; no remote workflow was dispatched.
