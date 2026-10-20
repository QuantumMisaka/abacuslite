# PR #8175 response drafts

Drafts, not posted. abacuslite 1.2.2 is published, with implementation merged
through [PR #11](https://github.com/QuantumMisaka/abacuslite/pull/11).
The [paired ABACUS harness](https://github.com/QuantumMisaka/abacus-develop/commit/7efe6422e6b3cf304cdd868885fbf434f0bfd17f)
is public on `fix/8175-public-api-contract` in the maintainer's fork. It has
not yet been applied to upstream PR #8175, whose default workflow still pins
1.1.0. The replies distinguish the published plugin from that pending update.

## Public API and behavior testing

Reply to [Growl1234's review](https://github.com/deepmodeling/abacus-develop/pull/8175#pullrequestreview-5574377766):

I agree that external integration tests need a supported API rather than
knowledge of the plugin's implementation. I have published
[abacuslite 1.2.2](https://pypi.org/project/abacuslite/1.2.2/) with the contract
and behavioral tests owned by the plugin, and prepared a paired follow-up
with real-engine integration checks retained under `interfaces/ASE_interface`.

The [plugin contract](https://github.com/QuantumMisaka/abacuslite/blob/v1.2.2/docs/public-api.md)
now names the supported calculator/profile, pure I/O,
selected running-log and k-point interfaces, including units, atom order,
missing values and deprecation rules. New tests exercise actual parsers and
calculator handoffs through public calls, including mixed engine formats in
one process and noncollinear results.

The [paired harness follow-up](https://github.com/QuantumMisaka/abacus-develop/commit/7efe6422e6b3cf304cdd868885fbf434f0bfd17f)
no longer inspects private reader switches or ASE
server/process objects, invokes asset-discovery helpers, or patches ASE's
global magnetic-property definitions. Independent raw-output comparisons
and numerical thresholds are preserved. Removing the registry patch exposed
a noncollinear result-projection defect, which is now fixed in the plugin
with a regression test.

The exact release tag's
[full CI run](https://github.com/QuantumMisaka/abacuslite/actions/runs/39384404829)
passed both installed-package and consumer lanes, plus nine real-engine tests
on each cold-built snapshot: develop `1bf602a` (beta11) and LTS `725bf475`
(3.10.1). The develop run includes socket handoff; both use the new harness.
The [release record](https://github.com/QuantumMisaka/abacuslite/blob/main/docs/superpowers/plans/2026-10-20-1.2.2-release.md)
identifies the source, artifact and validation evidence.

The harness follow-up depends on the plugin fix now available in 1.2.2. It is
public in my fork but has not yet been applied to this PR. This PR's workflow
still defaults to 1.1.0; the follow-up must update that stable version/hash
and validate the paired configuration before integration.

## Sustainable maintenance

Reply to [kirk0830's comment](https://github.com/deepmodeling/abacus-develop/pull/8175#issuecomment-6271080809):

I agree that moving the code into a personal repository does not by itself
provide sustainable maintenance. Alongside the published API and test changes,
I have prepared a
[concrete options document](https://github.com/QuantumMisaka/abacuslite/blob/v1.2.2/docs/maintenance-options.md)
with three possible arrangements:

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
