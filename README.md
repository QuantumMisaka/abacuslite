# abacuslite

## Introduction

abacuslite is a lightweight plugin for ABACUS (Atomic-orbital Based Ab-initio Computation at UStc), implementing the ASE (Atomic Simulation Environment) calculator interface.

### Key Features

- **Lightweight Design**: Implemented as a plugin, no need to modify ASE core code
- **Version Compatibility**: Candidate dependency range `ase>=3.28,<4`; supported combinations and validation limits are documented below.
- **ASE Integration**: Uses ASE as the running platform, making ABACUS a callable calculator within it
- **Function Support**: Provides SCF-based energy, force, and stress evaluations through ASE. ASE can use these evaluations for relaxation, molecular dynamics, NEB, band-structure, and density-of-states workflows.
- **Socket Support**: `AbacusSocketIO` provides fixed-cell i-PI socket calculations, with energy always available and forces/stress enabled independently when requested.

## Installation

This repository is the independent source package. `1.1.0rc1` is an unreleased
candidate; a successful source installation does not imply a PyPI release.
Install from this repository root:

```bash
python -m pip install .
```

ABACUS itself and the pseudopotential/orbital assets are supplied separately.
Pure input/output functions do not require an ABACUS executable:

```python
from abacuslite.io.generalio import read_input, read_stru
from abacuslite.io import legacyio, latestio

parameters = read_input("INPUT")
structure = read_stru("STRU")
```

Calculator imports remain `from abacuslite import Abacus, AbacusProfile,
AbacusSocketIO`. Choose the executable and assets explicitly as shown in the
examples. ATST workflow orchestration and consumer-specific result schemas
are outside this package.

## Validation and development

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
python -m build
python -m twine check --strict dist/*
```

Ordinary tests are offline; engine cases are skipped unless explicitly enabled:

```bash
export ABACUS_COMMAND='mpirun -np 2 abacus'
export ABACUS_PP_ORB=/absolute/path/to/ABACUS/tests/PP_ORB
export OMP_NUM_THREADS=1
python -m pytest --run-engine -m engine -q
```

The imported engine tests need their named ABACUS `tests/PP_ORB` assets and
include engine-specific numerical references. Do not interpret fixture tests
as validation of arbitrary engine versions. Package CI tests installed wheels
on Python 3.10 with minimum dependencies and Python 3.12 with current dependencies.
See [the implementation record](docs/superpowers/plans/2026-10-16-standalone-bootstrap.md)
for actual verification and remaining release work.

Each calculator retains its own output-reader selection. Parsing existing
output, including `eig_occ.txt`, is repeatable and does not consume source
files. The old compatibility switch only sets the default for new bare
templates. See [CHANGELOG.md](CHANGELOG.md) for migration differences.

## Usage Examples

Please refer to the example scripts in the `examples` folder. Recommended learning path:

1. **scf.py** - Basic SCF calculation example
2. **relax.py** - Atomic position relaxation calculation
3. **cellrelax.py** - Cell parameter relaxation calculation
4. **bandstructure.py** - Band structure calculation
5. **dos.py** - Density of states calculation
6. **md.py** - Molecular dynamics simulation
7. **constraintmd.py** - Constrained molecular dynamics simulation
8. **metadynamics.py** - Metadynamics simulation
9. **neb.py** - Nudged Elastic Band (NEB) calculation
10. **soc.py** - Noncollinear spin-orbit coupling calculation
11. **socketio.py** - Fixed-cell ASE optimization with `AbacusSocketIO`, running ABACUS as an i-PI socket client

The regular `Abacus` calculator runs one ABACUS calculation for each ASE property evaluation. ASE controls the relaxation, molecular-dynamics, and other workflow steps. The socket calculator reuses one ABACUS process for position updates, while the cell and electronic-structure settings remain fixed for that calculator instance.

## Authors

- Yuyang Ji
- Zhenxiong Shen
- Yike Huang
- Zhaoqing Liu

## Acknowledgments

Thanks to the ABACUS development team for their support and contributions.

## License

The applicable license terms are provided in [LICENSE](LICENSE). Source authors,
ABACUS provenance and ATST adaptations are recorded in [UPSTREAM.md](UPSTREAM.md).

## Contact

If you have any questions or suggestions, please contact us through:

- Plugin issues: [QuantumMisaka/abacuslite](https://github.com/QuantumMisaka/abacuslite/issues)
- ABACUS engine: [deepmodeling/abacus-develop](https://github.com/deepmodeling/abacus-develop)
