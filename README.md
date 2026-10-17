# abacuslite

A lightweight [ABACUS](https://github.com/deepmodeling/abacus-develop) calculator
and I/O plugin for [ASE](https://ase-lib.org/), combining the ABACUS interface
with general-purpose fixes from [ATST](https://github.com/QuantumMisaka/atst-tools).
It preserves the existing `abacuslite` imports and works without patching ASE.

Use it for energy, forces and stress in ASE calculations, or to read and write
ABACUS files without launching an engine. Both develop's newer output format
and LTS v3.10.x are supported; the fixed-cell socket calculator requires an
engine with socket support.

**Stable release:** [1.1.0 on PyPI](https://pypi.org/project/abacuslite/1.1.0/).
Develop/LTS interface checks have passed locally and on hosted CI.
See the [compatibility record](https://github.com/QuantumMisaka/abacuslite/blob/main/docs/compatibility-ci.md)
for tested snapshots and current gates, and the [release record](https://github.com/QuantumMisaka/abacuslite/blob/main/docs/superpowers/plans/2026-10-17-1.1.0-release.md)
for publication status.

## Installation

Requires **Python 3.10+** and **ASE 3.28+ (<4)**. From a POSIX shell:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install 'abacuslite==1.1.0'
python -m pip check
```

Pip installs ASE, NumPy and seekpath. ABACUS and its pseudopotential/orbital
assets are supplied separately. Existing environments and callers should
follow the [migration guide](https://github.com/QuantumMisaka/abacuslite/blob/v1.1.0/docs/migration.md).

## Quick start

Read an existing ABACUS input file without an engine:

```python
from abacuslite.io.generalio import read_input

parameters = read_input("INPUT")
print(parameters)
```

Examples are distributed in the source release. For a real calculation,
get the matching checkout, configure the engine and assets, and run an example:

```bash
git clone --branch v1.1.0 https://github.com/QuantumMisaka/abacuslite.git
cd abacuslite
export ABACUS_COMMAND='mpirun -np 2 abacus'
export ABACUS_PP_ORB=/absolute/path/to/ABACUS/tests/PP_ORB
export OMP_NUM_THREADS=1
python examples/scf.py
```

This example uses `genelpa`; select a solver supported by your ABACUS build.
The [usage guide](https://github.com/QuantumMisaka/abacuslite/blob/v1.1.0/docs/usage.md) lists required assets, example cleanup behavior,
calculator configuration and the complete example collection.

## Documentation

See the [documentation index](https://github.com/QuantumMisaka/abacuslite/blob/main/docs/README.md) for guides and current development records.

| Task | Guide |
| --- | --- |
| Configure calculators, read output, run examples | [Usage](https://github.com/QuantumMisaka/abacuslite/blob/v1.1.0/docs/usage.md) |
| Migrate ABACUS/ATST callers | [Migration](https://github.com/QuantumMisaka/abacuslite/blob/v1.1.0/docs/migration.md) |
| Set up development, run tests and validate packages | [Contributing](https://github.com/QuantumMisaka/abacuslite/blob/main/CONTRIBUTING.md) |
| Understand modules and package boundaries | [Module reference](https://github.com/QuantumMisaka/abacuslite/blob/v1.1.0/docs/reference.md) |
| Check supported engines, CI and acceptance evidence | [Compatibility](https://github.com/QuantumMisaka/abacuslite/blob/main/docs/compatibility-ci.md) |
| Review changes and source attribution | [Changelog](https://github.com/QuantumMisaka/abacuslite/blob/v1.1.0/CHANGELOG.md), [provenance](https://github.com/QuantumMisaka/abacuslite/blob/v1.1.0/UPSTREAM.md) |

## Authors and maintenance

- [Yuyang Ji (@jiyuyang)](https://github.com/jiyuyang)
- [Zhenxiong Shen (@Shen-Zhen-Xiong)](https://github.com/Shen-Zhen-Xiong)
- [Yike Huang (@kirk0830)](https://github.com/kirk0830)
- [Zhaoqing Liu (@QuantumMisaka)](https://github.com/QuantumMisaka)

The independent package is maintained by QuantumMisaka. Thanks to the ABACUS
and ATST contributors; original attribution is preserved in [UPSTREAM.md](https://github.com/QuantumMisaka/abacuslite/blob/v1.1.0/UPSTREAM.md).

Licensed under [LGPL-3.0-only](https://github.com/QuantumMisaka/abacuslite/blob/v1.1.0/LICENSE). Report plugin issues at
[QuantumMisaka/abacuslite](https://github.com/QuantumMisaka/abacuslite/issues).
