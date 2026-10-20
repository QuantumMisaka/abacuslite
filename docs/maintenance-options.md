# Maintenance options for community discussion

**Proposal, 2026-10-20. No ownership transfer, new maintainer appointment,
permission grant or commitment by another contributor is implied.**

ABACUS PR #8175 raises two separate concerns: external users need a stable
interface, and extracting the code must not leave one person solely responsible
for every future engine change and plugin release. The technical response is
the [public API contract](public-api.md), behavioral tests and engine-owned
integration checks. This document asks the community to choose a workable
maintenance arrangement.

## Goals shared by all options

- One authoritative source implementation, installable as `abacuslite` from
  PyPI without building or downloading the ABACUS engine.
- Preserve existing attribution, package identity, public imports and
  supported develop/LTS behavior.
- Permit a Python/parser fix to be released without waiting for a complete
  ABACUS engine release.
- Keep a contributor path open to the original authors and downstream users.
  Invitation does not imply that anyone has accepted maintenance duties.
- Make review, release access and handover workable when the principal
  contributor is unavailable.

## Options

| Topic | A: personal hosting, shared maintenance now | B: community-hosted independent repository | C: ABACUS monorepo subproject |
| --- | --- | --- | --- |
| Authoritative source | Current repository | Community repository, subject to acceptance | One directory in `abacus-develop` |
| Review and issue handling | Named willing collaborators with agreed access | Community team with named willing maintainers | Named plugin maintainers using ABACUS's review/issue process |
| Release cadence | Independent plugin releases | Independent plugin releases | Independent plugin versions/tags and directory-scoped package workflow |
| Coordinated engine/parser change | Linked PRs and candidate-pair checks | Linked PRs and candidate-pair checks | Can share a source PR; installed-package compatibility still tested |
| Setup cost | Confirm people, grant appropriate access, document release/handover | Community acceptance, repository transfer, access and publisher migration | Bring current plugin fixes/tests/history into the subproject; migrate publishing and retire the independent writable source |
| Continuity concern | Personal repository control remains a dependency | Organization hosting needs actual active maintainers | Shared repository access does not by itself supply plugin expertise or release attention |

**Recommendation for discussion:** A can establish shared responsibility
immediately if volunteers agree; B is a possible long-term home. C is equally
viable if the community prefers one development entry point and accepts
independent plugin releases. No option is selected by this proposal.

Do not add a submodule: issue #8165 already identified source-archive problems.
Do not maintain two editable implementations with bidirectional synchronization.
A read-only mirror is possible but does not solve maintenance staffing.

## Responsibilities to agree

These are proposed responsibilities, not appointments:

| Work | Proposed responsibility | Decision still needed |
| --- | --- | --- |
| Engine output, physics and socket producer | ABACUS change author coordinates affected adapter work and supplies engine evidence | Who reviews cross-boundary changes and tracks their completion? |
| Calculator/parser and supported API | Plugin maintainers review repairs and compatibility changes | Who accepts this role, with what practical availability? |
| ATST/Forge launcher/workflow/result policy | Respective downstream maintainers | Who receives compatibility notices and validates a candidate? |
| Plugin releases | An authorized release maintainer and an available alternate | Who can approve/publish and recover publisher configuration? |
| Issue triage and absence | A primary contact plus a documented alternate/handover route | Where are reports triaged, and how is temporary unavailability handled? |

Review permission, source administration, PyPI project ownership and Trusted
Publishing configuration are distinct. Decide who needs each permission;
grant only agreed access. A CODEOWNERS entry alone cannot ensure response
capacity or release recovery.

## Minimum evidence of a workable arrangement

1. At least one willing alternate is identified and has accepted a concrete
   review/release or recovery role. If nobody accepts, record the single-person
   risk honestly rather than describing the project as sustainably staffed.
2. A non-primary maintainer can follow the documented procedure to review a
   repair and prepare its checked artifacts. A local/TestPyPI rehearsal can
   establish this without publishing a production release.
3. Relevant repository and PyPI permissions are verified after authorization.
   Repository transfer does not automatically migrate PyPI administration.
4. An engine-format change has a clear route to adapter review and an
   installed candidate-pair check. A failed compatibility check has an owner.

## Migration and decision record

For A, retain existing artifacts and history while establishing agreed roles.
For B, preserve package identity and published tags/artifacts; update links,
repository permissions and the trusted publisher, and retire the old publisher
once the replacement is verified. For C, first import the current plugin
behavior and tests, establish the monorepo package/release workflow, and then
mark the former repository read-only with a clear contribution pointer.
Previously published PyPI versions must remain immutable under every option.

The main questions for discussion are:

1. Which option are the participating maintainers willing to operate?
2. Who accepts review, triage and release/recovery responsibility?
3. What evidence is required before removing the engine's embedded source?

Current status: **all three organizational decisions pending**. API cleanup
and behavior verification can proceed independently. Complete external-only
adoption should wait for an explicit upstream agreement; the existing open PR
is not evidence that this governance decision has already been made.
