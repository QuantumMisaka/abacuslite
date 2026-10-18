# Supported ABACUS versions

`abacuslite` supports the two output-format generations used by current
ABACUS releases. The table lists the snapshots covered by real-engine CI; it
is not a guarantee for every commit or build configuration.

| ABACUS snapshot | Output format | Reader | Socket | CI result |
| --- | --- | --- | --- | --- |
| develop `73cd094` (v3.11.0-beta10) | latest | `latestio` | yes | 9/9 |
| LTS `725bf47` (v3.10.1) | legacy | `legacyio` | no | 9/9 |

The engine jobs build both snapshots from clean source on Ubuntu 24.04
(CPU/LCAO, MPI, two build workers) and run nine checks per engine, including
socket on develop and a seeded native-MD case on LTS. The checks cover SCF,
ASE relaxation/MD, native MD, band structure, magnetic moments and socket
handoff. They are interface checks, not convergence studies. See
[compatibility and CI](compatibility-ci.md) for the detailed evidence.

## Reader selection

A calculator selects its reader from the configured executable's
`abacus --version` output:

- ABACUS 3.10.x uses `legacyio`.
- The tested develop 3.11 format uses `latestio`.
- Other revisions in these series are resolved by the same version rule but
  are not individually validated.

The selection belongs to each calculator instance. Creating a second
calculator does not change the reader of an existing one. For output-only
work, call `legacyio.read_abacus_out` or `latestio.read_abacus_out`
explicitly.

## Known limitations

- The tested LTS v3.10.1 build has no socket driver; use the regular
  `Abacus` calculator or a develop build for `AbacusSocketIO`.
- Output formats can change between develop commits. Re-run the engine
  checks when moving to a new snapshot.
- CI does not establish scientific convergence or equivalence between engine
  versions. Validate production settings and references for your system.

See [compatibility and CI](compatibility-ci.md) for revisions, environments
and retained evidence.
