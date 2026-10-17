# Compatibility checks across repositories

## Implemented here

`Package tests` runs on every PR and push, without path filters. The candidate
is built into wheel and sdist, metadata checked, installed and tested on
Python 3.10 with minimum dependencies and Python 3.12 with current dependencies.
The sdist is rebuilt and its wheel tested as well.

`installed-consumers` downloads the current PR's candidate wheel and builds a
wheel from the selected ATST source. It installs that same ATST wheel in two
separate environments: one with no independent plugin (vendored transition
backend), one with the candidate plugin (external backend). Both first receive
the same frozen `ATST[test]` dependency set; the candidate plugin is installed
without changing that set. ATST's installed-consumer runner checks import
provenance from outside the checkouts and runs the same ordinary offline suite
in both environments. Some ATST tests use repository-relative fixtures, so
pytest itself runs from the selected ATST root with installed-package origin
attested at session start and finish. The runner compares collection, outcome,
dependency, wheel and deterministic scientific/contract facts. Forge is then
installed in the external environment, where the plugin's `tests/consumers`
checks installed ATST and Forge behavior with literal ABACUS output fixtures.
These tests exercise SCF energy, ordered forces and Fermi level, periodic
frame matching and fail-closed behavior, native MD
cell/positions/forces, input and constant-potential guards, and Forge
legacy/latest fact projection. They also require mixed legacy/latest calculator
instances to remain isolated and repeated complete latest-output reads to
preserve `eig_occ.txt` and its energy, force and band facts. Only the engine
subprocess is replaced in the calculator tests; neither parser is used as the
other parser's oracle. This is an offline consumer contract gate, not a
real-engine or HPC workflow run.

Run the plugin-owned contracts locally from outside the checkouts after
installing the candidate wheel and both consumers:

```bash
python -m pytest tests/consumers --run-consumers -q -s
```

Ordinary pytest skips consumer tests so the plugin's own dependencies stay
small. `--run-consumers` must fail if its consumers are unavailable. Consumer
requirements do not become runtime dependencies of abacuslite.

PR jobs pin the reviewed ATST 2.2.9 integration revision `87caeedb` and
public Forge `43f5d4a` revision. These are reproducible compatibility baselines,
not permanent restrictions on consumer development. Update them through a
tested PR. Weekly scheduled jobs
use both consumer `main` heads to expose drift without making unrelated PRs
randomly fail. Failed scheduled runs need maintainer triage.

For a coordinated change, run this workflow from the candidate plugin branch
with `atst_ref` / `forge_ref` set to a consumer commit or `refs/pull/N/merge`.
The workflow prints resolved consumer SHAs and installed versions/paths. No
release or cross-repository write token is involved. Fork PRs run with read-only
permissions; do not switch candidate execution to privileged
`pull_request_target` or expose release secrets.

`compatibility-gate` runs even when dependencies fail/are skipped and accepts
only successful package and consumer jobs. It provides a stable status name
for a required check. **The repository currently has no branch protection or
ruleset.** CI failures are visible but do not yet enforce merge blocking.
Enabling required checks is a separate repository setting: require this gate
on `main` and keep approval/administrator-bypass policy explicit. Protect the
gate from being silently removed during workflow review. If merge queues are
introduced, add the `merge_group` trigger before requiring the gate there.

## Recommended adoption by ABACUS and ATST

These rows are the proposed target, not CI already installed in those repos.
The [ABACUS/ATST acceptance plan](superpowers/plans/2026-10-17-abacus-atst-integration-acceptance.md)
records refreshed source baselines, remaining migration work and the order of
engine, workflow and release verification before returning to Forge.

The earlier local integration tuple was ABACUS `bca8164`, ATST `53d6b7c`
and plugin `dc02043`. ABACUS passed nine CPU cases in both bundled and
external lanes, including native MD and socket. That ATST/plugin tuple passed
trusted GPU workflow acceptance for native MD, restart, serial/image-parallel
NEB, CP and a separately identified LTS reader check; its final CP marker
repair had targeted real-run evidence and an unchanged-path wheel diff.

The current ATST `87caeedb` and plugin `06f97b1` tuple has passed the full
offline installed-wheel vendored/external consumer comparison. Its paired GPU
job `1827672` also passed ten cases per backend, followed by explicit numeric
and artifact comparisons; these results bind the current production files
(`a56732c` ATST and `06f97b1` plugin) rather than reuse the earlier GPU tuple.
MD/NEB trajectories and vibration caches were audited, and external repeated
reads preserved the original files. These are bounded interface checks, not
scientific convergence certification for all workflows. These are local candidate results: neither consumer
PR has been created and GitHub Actions has not run on these changes. See the
plan for exact artifacts and evidence.

| Changed repository | Required PR verification | Coordinated candidate check | Scheduled compatibility |
| --- | --- | --- | --- |
| abacuslite | Candidate wheel + own contracts + installed consumers; affected real-engine evidence before parser/calculator release | Candidate wheel against selected engine and consumer PR refs | Supported engines and consumer heads |
| ABACUS | Build this PR's engine; install a validated plugin version; run engine integration harness with independent numeric references | Same engine binary with candidate plugin wheel/commit, before publishing the plugin | Develop engine with current released plugin and plugin main |
| ATST | Install this PR's ATST and supported plugin version(s); run external-backend tests and affected workflows | Candidate ATST plus candidate plugin, assert both imports are installed | Main ATST against latest plugin candidate/release |
| Forge | Candidate Forge plus optional installed plugin; retain native/parser projection and readonly regressions | Candidate plugin extra with candidate Forge | Main Forge with current plugin |

The historical ABACUS and ATST workflows guarded their bundled/vendored
copies. The local integration branches now add independent installed-plugin
lanes, but their new GitHub Actions workflows have not yet run remotely. The
ATST pin above is a local commit until its maintainer pushes it, so the
plugin's pinned checkout cannot resolve on GitHub before that publication.

ABACUS should retain its engine-side SCF/relax/MD/band/magnetic test harness,
assets, independent references and failure-directory upload while changing
where the plugin is installed. A thin import adapter is warranted only for a
real legacy caller. Do not add another full parser as a silent fallback.
Run from outside `interfaces/ASE_interface` and assert the imported path so
old source cannot shadow the installed candidate. Add socket engine coverage
where the engine supports it. Package fixture tests cannot replace this job.

ATST should exercise the installed external backend on its own PR head,
including profile policy, input/force ordering, Fermi retention and affected
NEB/constant-potential behavior. Keep expensive real-engine acceptance on
trusted infrastructure with a maintainer-controlled entry point; ordinary
community PRs must not submit HPC jobs. Existing vendored tests remain a
transition check until all direct imports have migrated, not the final gate.

## Develop and LTS engine coverage

LTS compatibility through `legacyio` is a required plugin responsibility,
confirmed by the maintainer on 2026-10-17. It does not depend on whether the
engine repository ships an ASE interface. `Abacus` obtains the version from
its configured executable and binds the chosen reader to that calculator;
v3.10.x uses `legacyio`. Explicit reader functions remain available for pure
I/O. Creating a develop calculator must not change an existing LTS instance.

The refreshed upstream references are develop `73cd094361f77574f9b28e825913e00f1d2c742a`
and LTS `725bf475a7159db4c1890a1f55160393e14b6b13`. Develop contains the bundled
plugin and engine-owned ASE workflow; LTS contains neither `interfaces/` nor
that workflow. The LTS documentation still describes the separate historical
`ase-abacus` distribution. Its absence of a bundled plugin does not mean LTS
is unsupported by abacuslite, and there is no LTS vendored baseline to compare.

Current CI coverage must be read in three separate layers:

- Plugin PR CI runs offline legacy/latest reader and instance-isolation tests
  on installed wheels. Its current workflow does not pass `--run-engine`, so
  it does not yet validate a real develop or LTS executable.
- Upstream develop's ASE PR job builds that engine checkout and tests its
  bundled plugin. Our local `bca8164` candidate additionally installs the
  independent wheel and runs the strengthened engine-owned suite outside the
  checkout. That candidate has not run remotely; its default plugin ref is
  still the historical `dc02043`, before both the `06f97b1` tolerance alignment
  and the `ba65f606` LTS/native-MD repairs.
- Current LTS has no abacuslite CI lane. Earlier v3.10.1 ATST relax evidence is
  useful but does not establish acceptance of the current LTS branch or all
  legacy I/O behavior. Fresh source-bound engine evidence is recorded in the
  [acceptance plan](superpowers/plans/2026-10-17-abacus-atst-integration-acceptance.md).

The current candidate repairs two issues exposed by real LTS execution:
`write_stru` now preserves ASE velocities in ABACUS atomic units and species
order, and `legacyio` reads native-MD geometry from `MD_dump` with physical
cells, Cartesian positions and periodic boundaries. Complete historical
single-log MD remains readable; an incomplete log or a corrupt existing dump
fails explicitly. The package's ordinary offline suite now includes retained
real LTS output and these compatibility regressions. This protects the observed
failures once the commits enter CI, but does not replace live engine jobs.

Local installed-wheel acceptance at `ba65f606` passed nine develop tests and
eight LTS tests against the exact source builds above, plus a seeded LTS
native-MD case with engine-generated initial velocities. Both native-MD paths
verify actual motion and compare every returned frame against raw engine
output. LTS correctly selects `legacyio`; socket is tested only on develop,
which has the corresponding driver. These short CPU/MPI interface cases do
not establish scientific equivalence between engine versions or support for
every engine feature. Detailed identities, failures and repaired-run evidence
are recorded in the acceptance plan.

Merely enabling the current `tests/integration` is insufficient: for example,
its SCF test prints the energy and its band test checks that a JSON file exists.
The stronger raw-property assertions currently live in the develop integration
candidate's engine-owned harness. The two-format engine gate must preserve
those observable checks for applicable legacy output rather than accept a
successful process or an existing output file as its only oracle.

The remaining engine gate should exercise the plugin PR's own wheel against
both a pinned develop engine and a pinned LTS engine, asserting actual
`latestio`/`legacyio` selection and installed import provenance. Use original
engine output to check energy, forces, stress, available Fermi/band/magnetic
facts and native-MD frames, with format-specific expectations where needed.
Do not require newer develop-only output files or socket capabilities from
LTS, and do not skip ordinary legacy behavior merely because LTS lacks the
newer ASE test directory. Scheduled branch-head checks supplement the pinned
PR gate. An LTS engine PR lane can consume the same external package and test
contract without copying the develop interface implementation into LTS.

Before activation, the develop candidate also needs an updated plugin pin,
an explicit path/hash binding to the freshly built executable, and matching
socket coverage in both lanes where the engine supports it. These are recorded
gaps, not already enabled checks. Engine tests must retain failed outputs and
nonzero exit statuses. Required-check activation is separate from a successful
job: the inspected develop effective rules only prohibit deletion and force
pushes; the branch-protection details endpoint was unavailable to this account.
No upstream branch settings were changed.

## Compatibility and coordinated changes

Protect public behavior: imports, inputs, units, atom ordering, missing values,
output artifacts, supported format selection and consumer handoff. Tests
should allow internal restructuring. Coverage percentages and source hashes
cannot show that a scientific result or a consumer handoff remains correct.

For an intentional break, document the contract and migration, add new behavior
coverage, introduce a compatible transition where practical, and validate the
candidate pair before changing dependency constraints. Link corresponding PRs
and retain the package/engine/consumer revision tuple and logs. Publish the
verified plugin before switching stable consumers to its indexed version.
Do not delete failing tests, loosen scientific tolerances or modify reference
values just to accept a refactor; a changed expectation needs an independent
scientific or contract rationale and review.

A refactor can pass its own repository's tests while breaking another. Each
repository's own PR must therefore gate its changed code, supplemented by
cross-repository candidate runs. A weekly job is an early warning, not a
substitute for required checks on the PR being merged.

GitHub references:
[required checks and skipped workflows](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks),
[protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches),
[privileged PR workflow security](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target).
