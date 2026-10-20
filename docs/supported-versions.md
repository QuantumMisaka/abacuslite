# Supported ABACUS versions

`abacuslite` supports the two output-format generations used by current
ABACUS releases. The table lists the snapshots covered by real-engine checks; it
is not a guarantee for every commit or build configuration.

| ABACUS snapshot | Output format | Reader | Socket | Schema | Checks |
| --- | --- | --- | --- | --- | --- |
| develop `1bf602a` (v3.11.0-beta11) | latest | `latestio` | yes | v1 | 9/9 |
| LTS `725bf47` (v3.10.1) | legacy | `legacyio` | no | — | 9/9 |

Both snapshots pass nine real-engine checks, including socket on develop and a
seeded native-MD case on LTS. The checks cover SCF, ASE relaxation/MD, native
MD, band structure, magnetic moments and socket handoff. They are interface
checks, not convergence studies. See
[compatibility and CI](compatibility-ci.md) for evidence.

The table records the published 1.2.2 acceptance. This release adds the
[public API contract](public-api.md) and fixes noncollinear result projection
without caller-side ASE registry changes. The tag workflow passed all nine
checks per engine using public-interface harness `7efe6422e`. Earlier local
paired-harness checks used develop `73cd094` (beta10) and the same LTS snapshot.
Exact source, artifact and hosted evidence is recorded in the
[1.2.2 release record](superpowers/plans/2026-10-20-1.2.2-release.md).

Socket support uses `abacus.socket.properties.v1`; the adapter rejects unknown
schemas. See the [socket adapter contract](socket-contract.md) for the
engine/adapter boundary.

## Reader selection

A calculator selects its reader from the configured executable's
`abacus --version` output:

- ABACUS 3.10.x uses `legacyio`.
- The tested develop 3.11 format uses `latestio`.
- Other revisions in these series are resolved by the same version rule but
  are not individually validated.

The selection belongs to each calculator instance; creating another calculator
leaves the existing reader unchanged. For output-only work, call
`legacyio.read_abacus_out` or `latestio.read_abacus_out` explicitly.

## Known limitations

- The tested LTS v3.10.1 build has no socket driver; use the regular
  `Abacus` calculator or a develop build for `AbacusSocketIO`.
- Output formats can change between develop commits. Re-run the engine
  checks when moving to a new snapshot.

See [compatibility and CI](compatibility-ci.md) for revisions, environments
and retained evidence.

## Energy metadata (1.2.1)

Both file readers preserve standard ASE energy values and expose the separate
no-entropy energy when available. See the [energy reference](reference.md#energy-metadata-121).
