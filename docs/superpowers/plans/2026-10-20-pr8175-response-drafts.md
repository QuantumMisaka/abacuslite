# PR #8175 response drafts

Local drafts, not posted. The implementation is retained on local branches
`fix/public-api-contract` (abacuslite) and `fix/8175-public-api-contract`
(ABACUS). Before posting, make the reviewed commits accessible and attach
their exact links plus the relevant CI evidence. Do not present local changes
as already available in the upstream PR or as a published release.

## Public API and behavior testing

Reply to [Growl1234's review](https://github.com/deepmodeling/abacus-develop/pull/8175#pullrequestreview-5574377766):

I agree that external integration tests need a supported API rather than
knowledge of the plugin's implementation. I have prepared a follow-up with
the contract and behavioral tests owned by abacuslite, and the real-engine
integration checks retained under `interfaces/ASE_interface`.

The plugin contract now names the supported calculator/profile, pure I/O,
selected running-log and k-point interfaces, including units, atom order,
missing values and deprecation rules. New tests exercise actual parsers and
calculator handoffs through public calls, including mixed engine formats in
one process and noncollinear results.

The ABACUS harness no longer inspects private reader switches or ASE
server/process objects, invokes asset-discovery helpers, or patches ASE's
global magnetic-property definitions. Independent raw-output comparisons
and numerical thresholds are preserved. Removing the registry patch exposed
a noncollinear result-projection defect, which is now fixed in the plugin
with a regression test.

Local validation of the unpublished 1.2.2.dev0 candidate passed: 231 source
and CI-helper tests, 185 installed-package tests in each of two environments,
10 installed consumer contracts, 20 harness checks, and 9 real-engine tests
on each of the retained develop and LTS snapshots. The develop run includes
socket handoff. These are local results, not hosted CI on the latest engine.
The detailed record identifies the exact revisions and artifacts.

The harness follow-up depends on the paired plugin fix. The current workflow
default, abacuslite 1.1.0, is not an acceptance target for these changes; a
reviewed candidate-pair CI run and a release/version/hash update are required
before integrating the follow-up.

## Sustainable maintenance

Reply to [kirk0830's comment](https://github.com/deepmodeling/abacus-develop/pull/8175#issuecomment-6271080809):

I agree that moving the code into a personal repository does not by itself
provide sustainable maintenance. I have prepared a concrete options document
alongside the API and test changes, with three possible arrangements:

1. Keep the current repository for now, with willing additional maintainers,
   agreed review/release access and an explicit handover route.
2. Transfer the independent package to a community repository if the community
   accepts it, preserving the package identity and independent release cadence.
3. Maintain abacuslite as an ABACUS monorepo subproject, with its own Python
   package versions and PyPI release pipeline.

All three retain one authoritative implementation and `pip install
abacuslite` without requiring an ABACUS build. The document compares setup
and migration costs and separates source administration, review, PyPI
ownership and publishing access.

My suggested interim step is shared maintenance in the current repository,
if volunteers accept concrete roles. Community hosting or a monorepo
subproject can then be chosen on its practical merits. No maintainer
appointment or community commitment is assumed. Before treating maintenance
as sustainable, we should identify an available alternate and demonstrate
that someone other than the principal contributor can prepare and validate
a release.

Could we discuss which arrangement people are willing to maintain, who can
accept review/triage/release responsibilities, and what evidence is needed
before removing the embedded source? The API contract and behavior tests
are useful under each arrangement and do not require settling repository
ownership first.
