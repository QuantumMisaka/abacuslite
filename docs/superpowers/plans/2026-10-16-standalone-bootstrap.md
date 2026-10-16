# Standalone package implementation

Authorization: the maintainer requested this repository and then authorized
continuing the related work on 2026-10-16. Scope for this delivery is the
independent source package, general-purpose compatibility fixes, tests,
documentation and GitHub source delivery. PyPI publication and changes to
ABACUS/ATST/Forge production dependencies follow candidate validation.

Design: [Independent ASE plugin](../../design.md).

## Tasks and acceptance

- [x] Import the latest ABACUS interface snapshot with author notices, LICENSE
  and source commit/history links. Baseline: ABACUS `4b92455ca`, snapshot
  `a1c7a4c`; plugin identical to the previously tested `8ae37fcd6` subtree.
- [x] Establish `src` packaging, standalone tests and offline/engine test
  separation. Keep public imports. Include fixtures and license in sdist;
  validate installed wheel and sdist-derived wheel outside the checkout.
- [x] Add regression evidence for point-KPT precision, missing/retained Fermi
  levels, SCF structure-frame matching and repeated read-only output parsing.
  Port reviewed ATST patches from `45d8c78` without replacing newer upstream
  socket and diagnostic code.
- [x] Reproduce mixed-calculator I/O selection failure, then isolate reader
  selection per calculator/template while preserving compatible entry points.
- [x] Run offline package tests and bounded installed consumer parity. Record
  exact environment, skips, failures and remaining real-engine coverage.
- [x] Add CI for tests and installation artifacts, source/compatibility docs
  and changelog. Do not enable an unverified PyPI publisher.
- [x] Independent review and resolution of material findings.
- [x] Commit and publish the validated source to the requested GitHub repository;
  verify the remote SHA and package CI.

## Rulings

- The newly cloned empty repository is isolated from all existing worktrees;
  implementation uses `bootstrap/standalone-package`, not an existing main.
- The initial import is an attributed snapshot, with original history linked;
  do not misrepresent it as preservation of every original Git commit.
- Preserve legacy real-engine tests and their assets requirements. Moving tests
  is a behavior-preserving operation; explicitly separate unexecuted engine
  cases rather than making ordinary pytest submit work or run an executable.
- A new candidate version identifies the merged implementation. It does not
  imply that 1.0.0 was ever published, or that 1.1.0rc1 is ready for PyPI.

## Evidence

Validated on 2026-10-16 after the Cartesian-unit repair:

| Boundary | Result |
| --- | --- |
| Built wheel, Python 3.10.20 / ASE 3.28.0 / NumPy 1.26.4 / seekpath 2.2.1 | 97 passed, 11 skipped, outside checkout |
| Built wheel, Python 3.12.13 / ASE 3.29.0 / NumPy 2.5.4 / seekpath 2.2.2 | 97 passed, 11 skipped, outside checkout |
| Wheel rebuilt from sdist, Python 3.10 environment, tests from extracted sdist | 97 passed, 11 skipped |
| Build, strict Twine metadata check, wheel license and sdist fixtures | Passed |
| Installed Forge consumer parity, Forge `1657d73` | 15 passed |
| Installed ATST profile/input contracts, ATST `45d8c78` | 32 passed |
| Joint installation of Forge, ATST and candidate package | Dependency check passed; ATST resolves external `abacuslite` |

The 11 skips comprise 9 real-engine cases and 2 retained upstream placeholder
cases. Python 3.12 checks expose ASE's NumPy 2.5 shape-assignment deprecation
warnings; no warning suppression was added.

Consumer evidence used scratch copies of existing suites: Forge's fixture root
was relocated to this project's source fixtures; ATST's explicit vendored
imports were redirected to the installed external package. Production consumer
code was installed unchanged. These bounded checks are not a production
migration or complete ATST/Forge acceptance.

Before repairs, focused regressions failed on point-KPT values, Fermi-level
handling, current-frame selection (4 failures), calculator reader isolation and
bare v3.9.0 selection reset (2 failures). Independent review found Cartesian
log coordinates needed multiplication by `alat_in_angstrom`; both reader
regressions reproduced the mismatch (2 failures) before the fix. They pass in
the installed suites above. The independent reviewer rechecked the repair and
reported no remaining blocking finding.

Source implementation `e984c44b2f4a251c745184ff4223ce943e844c37` was
pushed to `QuantumMisaka/abacuslite:main`; the remote SHA was verified.
[GitHub Actions run 38855256056](https://github.com/QuantumMisaka/abacuslite/actions/runs/38855256056)
passed both matrix jobs, including wheel tests, sdist rebuild, rebuilt-wheel
tests and artifact upload. The initial snapshot is `a1c7a4c`. Imported log
fixtures retain their original whitespace; source/document whitespace checks
exclude those byte-preserved fixtures.

## Remaining release and migration gates

- Run real ABACUS integration against the candidate and the intended engine
  versions, including socket coverage where supported. Fixture parity does not
  establish engine execution or scientific acceptance.
- Agree the exact ABACUS-side integration harness/compatibility wrapper; upstream
  adoption requires the ABACUS maintainers' acceptance.
- Configure PyPI ownership and Trusted Publishing, then publish the validated
  release artifacts with maintainer release authorization.
- Migrate consumer dependencies and remaining direct vendored imports, validate
  their release gates, and only then retire duplicated implementations.
