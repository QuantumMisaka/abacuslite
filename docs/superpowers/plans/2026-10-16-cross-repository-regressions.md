# Source integration audit and persistent consumer regressions

Authorization: on 2026-10-16 the maintainer accepted `1.1.0rc1`, requested
completing the independent package with ABACUS and ATST general fixes, and
asked how CI should protect community changes across the repositories.
Design: [Independent ASE plugin](../../design.md).

## Scope and acceptance

- [x] Refresh upstream refs and compare production definitions across ABACUS
  develop `4b92455ca`, ATST main `45d8c78` and independent `f36f366`.
  Record the disposition and behavioral coverage of every substantive difference.
- [x] Strengthen bidirectional calculator isolation and retain missing generic
  ATST regressions without duplicating tests already owned here. Demonstrate
  representative regressions catch broken behavior in isolated mutations.
- [x] Add opt-in installed ATST/Forge consumer tests and run them in GitHub CI
  against the candidate wheel. No vendored imports or local source shadowing.
  Keep consumer dependencies outside the runtime package requirements.
- [x] Document the actual CI state, per-repository PR/candidate/scheduled test
  responsibilities, engine evidence, and the required-check adoption boundary.
- [ ] Validate built distributions, independent review, commit and deliver the
  source changes with revision-bound local and GitHub evidence.

## Rulings

- Production definitions show no omitted registered ATST semantic fix: keep
  newer ABACUS implementations where they supersede old ATST code. Do not
  manufacture source changes merely to demonstrate integration work.
- Treat source comparison as an audit, not a code-identity CI gate. Behavior
  tests must permit equivalent implementations and intentional API evolution.
- This delivery implements CI in abacuslite. ABACUS and ATST adoption examples
  remain proposals, pending their own migration and owner review; no consumer
  production dependency switch, PyPI release or repository rule mutation.
- The native worktree tool targets the task's Forge repository and has no
  repository argument. Use an ignored Git worktree in the target abacuslite
  repository instead; preserve its verified main checkout.
- Required consumer jobs use reviewed public source revisions while there is
  no published plugin; manual candidate inputs allow coordinated PR testing.
  Moving branch heads belong to a separate scheduled compatibility check.

## Evidence

Baseline: package CI and local installed-wheel tests at `e984c44` passed
97 tests with 11 skips in both supported environments. Docs-only `f36f366`
did not change that implementation. Detailed new evidence follows below.


Local validation of the final implementation on 2026-10-16:

- Built wheel and sdist; strict Twine checks passed. Installed the candidate
  wheel in separate Python 3.10.20 and 3.12.13 environments. Tests copied
  outside all checkouts: **101 passed, 15 skipped** in each environment.
  Skips are 9 real-engine, 2 upstream placeholders and 4 opt-in consumers.
- Explicit installed consumer run: **4 passed** against ATST `45d8c78` and
  Forge `1657d73` (its relevant collection/parser/workspace production files
  are unchanged from the public `43f5d4a` CI baseline). Joint dependency check
  passed. No production parser or calculator source changed this round.
- Missing-consumer environment with `--run-consumers`: **4 errors**, as
  intended, rather than skipped tests passing the gate.
- Isolated mutation switching `read_results` back to the global reader:
  both creation-order regressions failed. This is retrospective mutation
  evidence for added coverage, not a new runtime bug fix.
- Executed aggregate-gate shell logic with successful, failed, skipped and
  cancelled dependency results; only success/success returned zero.
- Independent reviewer inspected the whole change and mutation evidence;
  no blocking issue remained. New CI still requires verification on GitHub.

The first draft of the consumer tests used the calculator energy convention
for Forge and list equality for KPT `nk`. Baseline failures were test errors:
Forge intentionally projects `E_KS(sigma->0)` when present, and `nk` is a tuple.
Expectations were corrected from the owning contract and raw fixture values;
no production behavior or numerical tolerance was weakened.
