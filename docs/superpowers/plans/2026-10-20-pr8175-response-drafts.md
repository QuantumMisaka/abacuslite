# PR #8175 review responses

Status: both responses posted on 2026-10-20 (UTC+08:00). This file retains
its original draft filename so existing links continue to resolve.

## Authorization and completed handoff

After publishing 1.2.2, the maintainer approved applying the reviewed harness
to PR #8175, updating its default plugin version/hash, running the actual PR
checks, and then sending the technical and maintenance responses. This
extended the earlier publication-only authorization; upstream merge,
repository transfer and maintainer appointments remain outside this scope.

Workflow: continuation of the L3 implementation/release plan. Evidence is
retained under `/home/james/scratch/abacuslite-pr8175-followup-20261020/`.

- [x] Append the reviewed harness and published wheel pin to
  `QuantumMisaka:integrate/external-abacuslite` without rewriting history.
- [x] Verify the installed package, offline harness and workflow; obtain
  focused independent review and pass the PR's hosted checks.
- [x] Update the PR description to the actual implementation and evidence;
  send the technical and maintenance responses.
- [x] Read back both comments and retain their exact text and public links.

## Source and verification

PR #8175 advanced from `1bf602a` through public-interface harness `7efe6422e`
to `ac64e83f7dee1521cbbd98f2da75375d337ab0cf`. The last commit changes only
the workflow's stable plugin version/hash and its README. The default now
installs published 1.2.2 and verifies wheel SHA256
`d4675aae2f70b99a6e18882e2c4ecf7f67f57eae10f5ba3e01622e879c6b8caf`.
Manual dispatch retains the reviewed candidate-ref path.

Local verification against an installed PyPI 1.2.2 package passed 20 offline
harness tests. Workflow YAML and embedded shell syntax checks passed; the pin
matches both PyPI and the release artifact. Staged and complete-follow-up
governance checks found no issues, and independent review found no blocker.
The earlier public-interface implementation review and dual-engine release
evidence remain in the [1.2.2 record](2026-10-20-1.2.2-release.md).

All reported current-head PR checks passed before posting, including the
GNU/Intel/CUDA build matrix, CPU/GPU tests, PyTest, governance, pre-commit and
both Read the Docs builds. The
[ASE workflow](https://github.com/deepmodeling/abacus-develop/actions/runs/39390096994)
passed 20 offline harness tests and nine real-engine cases, with no skips or
timeouts. It built PR merge checkout
`a410a97e32ade33831d7240b0a38e2a48c5f13cb`, whose parents include PR head
`ac64e83f7` and base `ffc4d0d3`. The report identifies ABACUS 3.11.0-beta11,
installed abacuslite 1.2.2 and report schema v2. The wheel identity and all
142 retained raw-output hashes were verified after downloading the artifact.

Both replies were posted as PR discussion comments, linking the original
review/comment and addressing the respective author. Their text and author
were verified by reading them back from GitHub. No review was dismissed,
no thread was marked resolved, and the upstream PR remains open. Maintenance
options remain proposals; participants still need to agree on ownership and
concrete review/release responsibilities.

## Technical response to Growl1234

Posted: [GitHub comment](https://github.com/deepmodeling/abacus-develop/pull/8175#issuecomment-6286787603)

@Growl1234 Following up on [your review](https://github.com/deepmodeling/abacus-develop/pull/8175#pullrequestreview-5574377766), this PR now includes the public-interface follow-up and uses published [abacuslite 1.2.2](https://pypi.org/project/abacuslite/1.2.2/) with its verified wheel SHA256. The updated head is `ac64e83f7`.

The plugin now owns an explicit [public API and compatibility contract](https://github.com/QuantumMisaka/abacuslite/blob/v1.2.2/docs/public-api.md), covering supported calculator/profile, I/O and k-point entry points, units, atom ordering, missing values and deprecation rules. Its [public-boundary tests](https://github.com/QuantumMisaka/abacuslite/blob/v1.2.2/tests/unit/test_public_api.py) exercise real parsers and calculator handoffs, including mixed develop/LTS formats and noncollinear results.

On the ABACUS side, the tests no longer inspect private reader switches or ASE server/process objects, use asset-discovery helpers, or patch ASE's global magnetic-property definitions. They retain independent raw-output assertions and numerical thresholds, with public socket close covered by the existing process-group timeout and nonzero-exit checks. Parser ownership and the canonical contract are linked from `interfaces/ASE_interface`.

Removing the magnetic registry patch exposed a result-projection defect, which was fixed in abacuslite 1.2.2 with a regression. Validation of this PR update: 20 offline harness tests passed against the published package, and the [current PR ASE CI](https://github.com/deepmodeling/abacus-develop/actions/runs/39390096994) passed all nine real-engine cases, including magnetic and socket checks. The job tested the PR merge checkout `a410a97e` containing this head; its reported wheel identity and 142 raw-output hashes were verified. Separately, the [1.2.2 tag CI](https://github.com/QuantumMisaka/abacuslite/actions/runs/39384404829) passed both installed-package/consumer lanes and all nine real-engine checks on each pinned develop/LTS snapshot.

## Maintenance response to kirk0830

Posted: [GitHub comment](https://github.com/deepmodeling/abacus-develop/pull/8175#issuecomment-6286802154)

@kirk0830 Regarding [your maintenance concern](https://github.com/deepmodeling/abacus-develop/pull/8175#issuecomment-6271080809), I agree that a personal repository alone does not establish sustainable maintenance. Alongside the published API contract and tests, I have added a [concrete options document](https://github.com/QuantumMisaka/abacuslite/blob/v1.2.2/docs/maintenance-options.md) for discussion:

1. Keep the current repository temporarily, with willing additional maintainers, agreed review/release access and a documented handover route.
2. Transfer the independent package to a community repository if accepted, preserving its package identity and independent release cadence.
3. Maintain abacuslite as an ABACUS monorepo subproject, with its own Python package versions and PyPI release pipeline.

All three keep one authoritative implementation and `pip install abacuslite` without requiring an ABACUS build. The API contract, plugin-owned behavioral tests and ABACUS-owned real-engine checks are already implemented and can be retained under any of these arrangements.

My suggested interim step is shared maintenance in the current repository, if volunteers accept concrete roles; community hosting or a monorepo subproject can then be chosen on its practical merits. No appointment or community commitment is assumed. Repository access, PyPI ownership and publishing permissions are separate responsibilities. Before describing the arrangement as sustainable, we should identify an available alternate and demonstrate that someone other than the principal contributor can prepare and validate a release.

Could we discuss which arrangement the participating maintainers are willing to operate, who can accept review/triage/release responsibilities, and what evidence is needed before removing the embedded source? I would like to settle that maintenance arrangement explicitly before upstream adoption.
