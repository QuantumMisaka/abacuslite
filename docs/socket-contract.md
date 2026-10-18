# Socket adapter contract

`AbacusSocketIO` is the ASE-side adapter for the ABACUS fixed-cell i-PI
socket driver. The engine-side wire format and input parameters are owned by
ABACUS; this page defines what the adapter relies on and how changes are
coordinated.

Canonical engine documentation:
[ABACUS ASE interface](https://github.com/deepmodeling/abacus-develop/blob/develop/docs/advanced/interface/ase.md).

## Protocol version

The adapter accepts the metadata schema
`abacus.socket.properties.v1` and rejects unknown schemas. Additive fields may
be added within v1; a breaking change requires a new schema version and a
transition window in both repositories.

The engine-side schema identifier is defined in
`source/source_relax/socket_utils.h` (`kPropertiesSchema`) and covered by the
ABACUS socket driver unit test.

## What the adapter relies on

| Item | Contract |
| --- | --- |
| Endpoint | `ABACUS_SOCKET_ADDRESS=host:port` for TCP or `/tmp/ipi_<name>:UNIX` for a UNIX socket |
| Mode | `calculation=scf` with `socket_driver=1` |
| Fixed state | Cell, species, atom count and electronic-structure settings stay fixed; only positions change |
| Properties | Energy is always present; forces and stress are independently enabled by `cal_force` / `cal_stress` |
| Metadata | `schema`, `present` and `scf_converged` describe the returned frame |
| Padding | Disabled properties are protocol padding and are not reported as physical zeros |
| Ordering | The adapter maps ASE atom order to the socket order and restores forces to ASE order |
| Nonconvergence | `scf_converged=false` is returned with available results; the caller chooses whether to accept them |
| Failure | Invalid metadata, stale results or an unsupported schema fail closed and clear the previous frame |

## CI gates

- ABACUS owns the socket driver tests and the engine-side socket handoff.
- The ABACUS ASE workflow installs the published `abacuslite` wheel, or a
  reviewed candidate ref, and runs the socket handoff against the engine built
  from that PR.
- abacuslite builds pinned ABACUS develop and LTS snapshots and runs the
  socket handoff in the develop lane. LTS has no socket driver; that is a
  declared capability difference, not a skipped requirement.
- Scheduled runs resolve the ABACUS develop head and include the socket case,
  so wire-format drift is detected without a release.

## Change rule

For an additive change, update the engine and adapter tests, then update
[supported versions](supported-versions.md). For a breaking change, add a new
schema version and make the adapter accept both versions before the engine
stops emitting the old one. Engine and adapter PRs must link to each other.

See [From ase-abacus to abacuslite](ase-interface.md) for the adapter
architecture and [UPSTREAM.md](../UPSTREAM.md) for socket provenance.
