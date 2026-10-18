# abacuslite

## Introduction

A lightweight ABACUS calculator and I/O plugin for ASE. It packages ABACUS's
ASE interface as an independent, pip-installable project. Existing
`abacuslite` imports keep working, and ASE does not need patching.

Use it for energy, forces and stress in ASE workflows, or to read and write
ABACUS files without launching an engine. The current develop output format
and the 3.10.x LTS format are supported. The fixed-cell socket calculator
requires an ABACUS build with the socket driver.

**Release line:** `1.1.1` (candidate; publication pending authorization). It
adds calculator, restart and default-path corrections on top of `1.1.0`; the
1.1.x line was tested with ABACUS develop `v3.11.0-beta10` and LTS `v3.10.1`. See the
[compatibility record](https://github.com/QuantumMisaka/abacuslite/blob/main/docs/compatibility-ci.md)
for the exact snapshots and current checks, and the
[release record](https://github.com/QuantumMisaka/abacuslite/blob/main/docs/superpowers/plans/2026-10-19-1.1.1-release.md)
for artifact and publication status.

### Key features

- **Lightweight:** an ASE plugin; no ASE core changes are required.
- **Engine compatibility:** each calculator selects `latestio` or `legacyio`
  from the configured ABACUS version.
- **ASE workflows:** energy, forces and stress for relaxation, MD, NEB,
  band structure and DOS through ASE.
- **Socket support:** `AbacusSocketIO` provides fixed-cell i-PI calculations.
- **Pure I/O:** read and write INPUT, STRU and KPT, and read completed output
  without launching ABACUS.

## Installation

Requires **Python 3.10+** and **ASE 3.28+ (<4)**:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install 'abacuslite==1.1.1'
python -m pip check
```

Pip installs ASE, NumPy and seekpath. ABACUS, pseudopotentials and orbital
files are supplied separately. Tested engine snapshots are listed in
[supported versions](https://github.com/QuantumMisaka/abacuslite/blob/main/docs/supported-versions.md).

## Quick start

Read an existing input file without an engine:

```python
from abacuslite.io.generalio import read_input

print(read_input("INPUT"))
```

Run a short SCF calculation:

```python
from ase.build import bulk
from abacuslite import Abacus, AbacusProfile

atoms = bulk("Si", "diamond", a=5.43)
profile = AbacusProfile(
    command="mpirun -np 2 abacus",   # or the actual ABACUS binary path
    pseudo_dir="/path/to/PP_ORB",
    orbital_dir="/path/to/PP_ORB",
)
atoms.calc = Abacus(
    profile=profile,
    directory="scf-run",
    pseudopotentials={"Si": "Si_ONCV_PBE-1.0.upf"},
    basissets={"Si": "Si_gga_8au_100Ry_2s2p1d.orb"},
    inp={"basis_type": "lcao", "gamma_only": True, "scf_thr": 1e-3},
)
print(atoms.get_potential_energy())
```

Recent ABACUS develop builds may name the executable `abacus_basic_para`
instead of `abacus`; point `command` at the actual binary. Most shipped
examples use `genelpa`; if your build lacks it, set `ks_solver` to an available
solver.

## Examples

The source release includes eleven examples. A suggested learning path is
SCF, relaxation or MD, then the more specialized workflows. See the
[usage guide](https://github.com/QuantumMisaka/abacuslite/blob/main/docs/usage.md)
for assets, engine features, cleanup behavior and the complete table.

| Example | Purpose |
| --- | --- |
| [scf.py](https://github.com/QuantumMisaka/abacuslite/blob/main/examples/scf.py) | SCF calculation of silicon |
| [relax.py](https://github.com/QuantumMisaka/abacuslite/blob/main/examples/relax.py) | Atomic position relaxation |
| [cellrelax.py](https://github.com/QuantumMisaka/abacuslite/blob/main/examples/cellrelax.py) | Cell relaxation |
| [bandstructure.py](https://github.com/QuantumMisaka/abacuslite/blob/main/examples/bandstructure.py) | Band structure |
| [dos.py](https://github.com/QuantumMisaka/abacuslite/blob/main/examples/dos.py) | Density of states |
| [md.py](https://github.com/QuantumMisaka/abacuslite/blob/main/examples/md.py) | Molecular dynamics |
| [constraintmd.py](https://github.com/QuantumMisaka/abacuslite/blob/main/examples/constraintmd.py) | Constrained molecular dynamics |
| [metadynamics.py](https://github.com/QuantumMisaka/abacuslite/blob/main/examples/metadynamics.py) | Metadynamics with PLUMED |
| [neb.py](https://github.com/QuantumMisaka/abacuslite/blob/main/examples/neb.py) | Nudged elastic band |
| [soc.py](https://github.com/QuantumMisaka/abacuslite/blob/main/examples/soc.py) | Noncollinear spin-orbit coupling |
| [socketio.py](https://github.com/QuantumMisaka/abacuslite/blob/main/examples/socketio.py) | Fixed-cell socket calculations |

## Documentation

| Task | Guide |
| --- | --- |
| Configure calculators, read output, run examples | [Usage](https://github.com/QuantumMisaka/abacuslite/blob/main/docs/usage.md) |
| Check tested engines and limitations | [Supported versions](https://github.com/QuantumMisaka/abacuslite/blob/main/docs/supported-versions.md) |
| Fix common setup and runtime problems | [Troubleshooting](https://github.com/QuantumMisaka/abacuslite/blob/main/docs/troubleshooting.md) |
| Migrate ABACUS/ATST callers | [Migration](https://github.com/QuantumMisaka/abacuslite/blob/main/docs/migration.md) |
| Understand modules and package boundaries | [Module reference](https://github.com/QuantumMisaka/abacuslite/blob/main/docs/reference.md) |
| Check CI and acceptance evidence | [Compatibility](https://github.com/QuantumMisaka/abacuslite/blob/main/docs/compatibility-ci.md) |
| Set up development and run tests | [Contributing](https://github.com/QuantumMisaka/abacuslite/blob/main/CONTRIBUTING.md) |
| Review changes and attribution | [Changelog](https://github.com/QuantumMisaka/abacuslite/blob/main/CHANGELOG.md), [provenance](https://github.com/QuantumMisaka/abacuslite/blob/main/UPSTREAM.md) |

## Authors

- [Yuyang Ji (@jiyuyang)](https://github.com/jiyuyang)
- [Zhenxiong Shen (@Shen-Zhen-Xiong)](https://github.com/Shen-Zhen-Xiong)
- [Yike Huang (@kirk0830)](https://github.com/kirk0830)
- [Zhaoqing Liu (@QuantumMisaka)](https://github.com/QuantumMisaka)

## Contributors

- [Jianrui Geng (@Phorbol)](https://github.com/Phorbol) — fixed-cell i-PI
  socket driver and `AbacusSocketIO` (ABACUS #7609).

## Acknowledgments

Thanks to the ABACUS community for their support and contributions.

## License

Licensed under [LGPL-3.0-only](https://github.com/QuantumMisaka/abacuslite/blob/main/LICENSE).
Original attribution and ATST-derived adaptations are recorded in
[UPSTREAM.md](https://github.com/QuantumMisaka/abacuslite/blob/main/UPSTREAM.md).

## Contact

Report issues at [QuantumMisaka/abacuslite](https://github.com/QuantumMisaka/abacuslite/issues).
