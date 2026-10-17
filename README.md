# abacuslite

## Introduction

abacuslite is a lightweight plugin for ABACUS (Atomic-orbital Based Ab-initio Computation at UStc), implementing the ASE (Atomic Simulation Environment) calculator interface.

### Key Features

- **Lightweight Design**: Implemented as a plugin, no need to modify ASE core code
- **Version Compatibility**: Candidate dependency range `ase>=3.28,<4`; supported combinations and validation limits are documented below.
- **ASE Integration**: Uses ASE as the running platform, making ABACUS a callable calculator within it
- **Function Support**: Provides SCF-based energy, force, and stress evaluations through ASE. ASE can use these evaluations for relaxation, molecular dynamics, NEB, band-structure, and density-of-states workflows.
- **Socket Support**: `AbacusSocketIO` provides fixed-cell i-PI socket calculations, with energy always available and forces/stress enabled independently when requested.

## Architecture and source continuity

The package follows the original ABACUS ASE interface design. It combines the
current ABACUS implementation with ATST's general-purpose fixes while keeping
the same calculator classes and I/O module paths:

| Module | Responsibility |
| --- | --- |
| `core.py` | `AbacusProfile`, `AbacusTemplate`, ASE `Abacus` calculator and `AbacusSocketIO` |
| `io/generalio.py` | INPUT, STRU and KPT reading/writing |
| `io/legacyio.py`, `io/latestio.py` | Readers for the two existing ABACUS output formats |
| `utils/ksampling.py` | K-point paths and sampling helpers |

```text
src/abacuslite/         # original runtime modules, now in a src layout
examples/              # ASE usage examples, with external engine/assets
tests/                 # offline, engine and installed-consumer tests + fixtures
```

Moving the source under `src/` changes packaging, not `import abacuslite`.
Tests formerly embedded in production modules now live under `tests/`.
ASE still owns optimization/MD/NEB algorithms; ATST owns its workflow and
launcher policy. Neither ATST nor Forge is a runtime dependency of this plugin.
See [DEVELOP.md](DEVELOP.md) for the module reference and
[the integration audit](docs/upstream-integration.md) for the preserved ABACUS
features and integrated ATST fixes.

## Installation

Requires **Python 3.10+**. `1.1.0rc1` is an unreleased candidate; install from
this repository until an indexed release is available. From a fresh checkout:

```bash
git clone https://github.com/QuantumMisaka/abacuslite.git
cd abacuslite
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
python -m pip check
python -c "import abacuslite; print(abacuslite.__file__)"
```

The activation command above is for POSIX shells. If you already have a suitable
Python environment, use it directly. Runtime dependencies are ASE, NumPy and
seekpath; the currently tested combinations use Python 3.10 / ASE 3.28 and
Python 3.12 / ASE 3.29. The declared dependency range is not a promise that every
future combination is validated.

For development, use `python -m pip install -e '.[dev]'`. Wheel and sdist builds
are supported; downstream CI should record the exact candidate commit or wheel used for verification.

ABACUS itself and the pseudopotential/orbital assets are supplied separately.
Compatibility with the ABACUS LTS branch is part of this plugin's scope even
though LTS does not contain `interfaces/ASE_interface`. `Abacus` selects
`legacyio` for a v3.10.x engine from its actual `--version` output; each
calculator retains its own selection. Develop engines using the newer output
format select `latestio`. See the [engine compatibility checks](docs/compatibility-ci.md#develop-and-lts-engine-coverage)
for the distinction between reader regressions and real-engine acceptance.

Pure input/output functions do not require an ABACUS executable:

```python
from abacuslite.io.generalio import read_input, read_stru
from abacuslite.io import legacyio, latestio

parameters = read_input("INPUT")
structure = read_stru("STRU")
```

The public calculator imports are unchanged:

```python
from abacuslite import Abacus, AbacusProfile, AbacusSocketIO
```

To run the SCF example, supply an installed ABACUS executable and matching assets:

```bash
export ABACUS_COMMAND='mpirun -np 2 abacus'
export ABACUS_PP_ORB=/absolute/path/to/ABACUS/tests/PP_ORB
export OMP_NUM_THREADS=1
python examples/scf.py
```

`ABACUS_PP_ORB` can instead point to your own asset directory. `scf.py` requires
`Si_ONCV_PBE-1.0.upf` and `Si_gga_8au_100Ry_2s2p1d.orb`; other examples name their
own assets. Set engine parameters, including the eigensolver, to match your
ABACUS build. The example scripts read these environment variables explicitly;
the library itself continues to take command/asset settings through
`AbacusProfile`. There is no automatic ASE installation patch or engine download.

## Migrating existing callers

Normal callers retain `from abacuslite import ...` and `abacuslite.io.*` imports.
The installation source changes from `interfaces/ASE_interface` to this package.
ATST workflow callers continue using ATST; maintainers must route direct
vendored calculator imports through its backend adapter and pure I/O imports
through `abacuslite.io` before removing the bundled copy.

Migration differences are explicit: the ASE floor is now 3.28, `eig_occ.txt` is
not deleted when read, and the compatibility reader switch only affects newly
created bare templates. A calculator with a profile keeps its own reader.
See [the migration guide](docs/migration.md) for installation-path checks,
consumer-specific steps and remaining engine validation.

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
for the initial extraction, and [the CI record](docs/superpowers/plans/2026-10-16-cross-repository-regressions.md)
for subsequent installed-consumer verification.

Each calculator retains its own output-reader selection. Parsing existing
output, including `eig_occ.txt`, is repeatable and does not consume source
files. The old compatibility switch only sets the default for new bare
templates. See [CHANGELOG.md](CHANGELOG.md) for migration differences.

The [integration audit](docs/upstream-integration.md) maps ABACUS and ATST fixes
to their regression coverage and explains reader instance isolation. See the
[cross-repository CI guide](docs/compatibility-ci.md) and
[contributor guide](CONTRIBUTING.md) for PR and coordinated-change checks.

## Usage Examples

The scripts in `examples/` preserve the upstream ASE usage patterns. All accept
`ABACUS_PP_ORB` and `ABACUS_COMMAND`; the latter overrides their original launcher
default. Some examples remove their calculation directories on completion, so
use a dedicated checkout or copy when adapting them for retained results.
Metadynamics additionally needs a working PLUMED installation. These are usage
examples; offline startup checks do not certify their full scientific workflows.
Recommended learning path:

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
