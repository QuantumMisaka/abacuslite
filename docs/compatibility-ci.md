# Compatibility checks across repositories

## Implemented here

`Package tests` runs on every PR and push, without path filters. The candidate
is built into wheel and sdist, metadata checked, installed and tested on
Python 3.10 with minimum dependencies and Python 3.12 with current dependencies.
The sdist is rebuilt and its wheel tested as well.

`installed-consumers` downloads the same candidate wheel, installs actual ATST
and Forge packages, checks dependencies, and runs `tests/consumers` outside all
checkouts. Tests require installed imports and ATST's external backend; missing
consumer packages or a vendored fallback fail an explicitly requested run.
They exercise ATST input preparation and ASE calculator force/Fermi handoff,
and Forge legacy/latest fact projection with literal fixture expectations.
Only the ABACUS subprocess is substituted in the ATST calculator test. This is
an offline consumer contract check, not a real engine or full workflow test.

Run locally after installing the candidate wheel and both consumers:

```bash
python -m pytest tests/consumers --run-consumers -q -s
```

Ordinary pytest skips consumer tests so the plugin's own dependencies stay
small. `--run-consumers` must fail if its consumers are unavailable. Consumer
requirements do not become runtime dependencies of abacuslite.

PR jobs use reviewed ATST `45d8c78` and public Forge `43f5d4a` revisions. These
are reproducible compatibility baselines, not permanent restrictions on
consumer development. Update them through a tested PR. Weekly scheduled jobs
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

| Changed repository | Required PR verification | Coordinated candidate check | Scheduled compatibility |
| --- | --- | --- | --- |
| abacuslite | Candidate wheel + own contracts + installed consumers; affected real-engine evidence before parser/calculator release | Candidate wheel against selected engine and consumer PR refs | Supported engines and consumer heads |
| ABACUS | Build this PR's engine; install a validated plugin version; run engine integration harness with independent numeric references | Same engine binary with candidate plugin wheel/commit, before publishing the plugin | Develop engine with current released plugin and plugin main |
| ATST | Install this PR's ATST and supported plugin version(s); run external-backend tests and affected workflows | Candidate ATST plus candidate plugin, assert both imports are installed | Main ATST against latest plugin candidate/release |
| Forge | Candidate Forge plus optional installed plugin; retain native/parser projection and readonly regressions | Candidate plugin extra with candidate Forge | Main Forge with current plugin |

At this audit, ABACUS `.github/workflows/ase_plugin_test.yml` builds its PR
engine but installs `interfaces/ASE_interface` from the same tree. ATST's
interface workflow validates a pinned vendored snapshot; ordinary tests do
not install the independent plugin. Those jobs remain useful, but neither
currently protects the new independent package boundary.

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
