# Public API and maintenance discussion follow-up

## Authorization and scope

The maintainer approved this work in the 2026-10-20 conversation following
ABACUS PR #8175 reviews: implement the public interface contract, behavioral
tests and engine-side integration corrections; prepare concrete maintenance
options for community discussion. Repository ownership remains undecided.
Do not publish packages, send review replies, transfer permissions or merge
the external-only adoption as part of this work.

Baselines: abacuslite `347a936`; ABACUS PR #8175 `1bf602a`.
Working branches: plugin `fix/public-api-contract`, engine harness
`fix/8175-public-api-contract`. The existing plugin checkout is preserved.

## Outcomes and acceptance

- [x] Define the supported calculator/I/O/k-point interfaces and observable
  result, ordering, missing-value, exception and compatibility rules in the
  plugin. Audit existing engine and ATST/Forge calls; retain historical imports.
- [x] Exercise the published surface with real parsers and a controlled
  engine boundary, including mixed-format calculator isolation, SCF frame
  selection, optional energy metadata and noncollinear moments. Preserve
  existing tests; regression-first evidence for any runtime repair.
- [x] Remove engine-harness dependencies on private reader state and asset
  discovery. Keep independent raw-output assertions and provenance checks.
  Use public socket lifecycle operations with process isolation owned by the
  harness. Do not modify ASE's global magnetic-property registry.
- [x] Document the engine-side entry point, parser ownership and linked
  contract without duplicating the parser or its API specification.
- [x] Prepare three maintenance options with responsibilities, release
  authority, continuity and migration costs explicitly pending community
  agreement. Prepare local response drafts tied to actual delivered evidence.
- [x] Run offline baseline/candidate checks, installed wheel/sdist checks,
  available develop/LTS engine checks and an independent review; record exact
  scope and remaining upstream/hosted validation separately.

## Implementation rulings

- Public behavior is the acceptance boundary; no reader-selection getter is
  added solely for tests. Engine-format mismatches are detected from version
  information and real output assertions.
- Fixed engine fixtures use explicit asset filenames. Existing `load_pseudo`
  and `load_orbital` imports remain available for compatibility; they are not
  expanded into an asset-provisioning API.
- The socket case now uses public `close()` within the existing process-group
  timeout. ASE's nonzero-client-exit warning is promoted to a failing error
  locally during close; raw output and timeout failures remain preserved.
- Removing the noncollinear registry patch exposed an adapter defect:
  ASE `Properties` rejects vector moments. The plugin now projects other
  properties through ASE and retains vector moments without mutating global
  definitions or the parsed calculator. The magnetic cases remain required.
- ATST/Forge already consume five running-log helpers. These are explicitly
  supported in both reader modules, with partial-log, unit and absence rules
  and public-boundary tests. This task does not change downstream runtimes or
  expand asset/workflow ownership.
- The candidate is `1.2.2.dev0`, distinct from published 1.2.1. No tag or
  published artifact is changed. The engine report uses schema v2 because
  private reader-selection fields were removed.

## Evidence

All results below are local, from 2026-10-20. Logs, installed environments,
artifacts and raw engine outputs are retained under
`/home/james/scratch/abacuslite-public-api-20261020/`.

| Check | Result | Evidence relative to that directory |
| --- | --- | --- |
| Plugin baseline, source plus CI helper tests | 216 passed, 19 opt-in skips | `plugin-baseline.log` |
| Harness baseline with the intended source plugin | 16 passed | `harness-baseline.log` |
| Public-boundary regression before repair | Both noncollinear formats failed with vector `magmoms` shape rejection; 7 other cases passed | `public-api-red.log` |
| Candidate source plus CI helper tests | 231 passed, 19 opt-in skips | `plugin-full.log` |
| Installed wheel outside checkout, Python 3.12 / ASE 3.29 | 185 passed, 19 opt-in skips | `wheel-current.log` |
| Installed wheel outside checkout, Python 3.10 / ASE 3.28 | 185 passed, 19 opt-in skips | `wheel-min.log` |
| Wheel rebuilt from sdist, tests from extracted sdist, Python 3.10 | 185 passed, 19 opt-in skips | `sdist-min.log` |
| Installed consumer contracts, ATST 2.3.1 and Forge `d8d1a74736ef0d8f1e5d4dab09662ceb370afaf5` | 10 passed; dependency check clean | `consumers-current.log`, `consumer-install.log` |
| Engine harness after review repairs | 20 passed | `harness-final.log` |
| Real develop engine, 3.11.0-beta10 at `73cd094361f77574f9b28e825913e00f1d2c742a` | 9 passed, including socket and three magnetic cases; no skips/timeouts | `engine-develop/evidence.json` and case logs |
| Real LTS engine, 3.10.1 at `725bf475a7159db4c1890a1f55160393e14b6b13` | 9 passed, including generated native MD and three magnetic cases; no skips/timeouts | `engine-lts/evidence.json` and case logs |

The 19 ordinary-suite skips are explicitly opt-in engine/consumer tests;
the consumer and dual-engine results above are separate runs. The consumer
scope is the plugin-owned contract suite, not the complete downstream suites.
An initial harness baseline accidentally used an older installed 1.1.0rc1
plugin; its MD failure was an environment mismatch. The recorded passing
baseline explicitly selected the intended source.

Both engine runs used the installed candidate wheel in a Python 3.12 / ASE
3.29 Docker environment and two MPI ranks. They reused retained compiled
binaries from the 2026-10-18 dual-engine acceptance. This is not a fresh engine
build or a check of a newer develop revision. Reports bind executable hashes,
wheel identity, harness content and raw artifacts; all 142 develop and 141 LTS
raw-file hashes were rechecked.

An independent same-family reviewer inspected both working trees. Two findings
were repaired: public socket close must still reject a nonzero client exit,
and `write_kpt` documentation must not promise unsupported line-mode writing.
The socket regression first failed (`socket-close-red.log`); the final harness
suite passed. The reviewer reran both close checks and reported no remaining
blocking findings in the targeted follow-up.

Final packaging includes the reviewed documentation and this delivery record.
The final wheel runtime and sdist runtime/test/fixture payloads are checked
against the tested artifacts; hashes and comparison results are retained in
`final-artifact-check.json`. The final wheel and sdist must pass strict Twine
validation before local delivery.

## Delivery and integration boundary

Reviewable outputs: [public API](../../public-api.md),
[maintenance options](../../maintenance-options.md), and
[unsent PR response drafts](2026-10-20-pr8175-response-drafts.md).
Both implementation branches/worktrees are retained locally.

No package has been published, no review reply sent, and no ownership or
permission change made. No hosted CI run is claimed for these candidates.
PR #8175's existing default workflow still pins published 1.1.0, which lacks
the noncollinear repair. Before upstream integration, expose the reviewed
plugin commit for candidate-pair CI, obtain the required publication decision,
publish the reviewed plugin and update the workflow version/hash together.
External-only adoption also needs an explicit community maintenance agreement.
