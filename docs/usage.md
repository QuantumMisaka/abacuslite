# Using abacuslite

Install the package following the [README](../README.md#installation).
The runtime depends on ASE, NumPy and seekpath. Tested package combinations
include Python 3.10 / ASE 3.28 and Python 3.12 / ASE 3.29; the declared
dependency range is not a guarantee for every future combination.
Tested ABACUS snapshots are listed in [supported versions](supported-versions.md);
common setup problems are covered in [troubleshooting](troubleshooting.md).

## Configure a calculator

The public calculator imports are:

```python
from abacuslite import Abacus, AbacusProfile, AbacusSocketIO
```

`AbacusProfile` supplies the engine command, pseudopotential/orbital directories
and OpenMP settings. Pass that profile to `Abacus` along with a calculation
directory, pseudopotential/orbital filenames and ABACUS input parameters; then
attach the calculator to an ASE `Atoms` object. The complete
[SCF example](../examples/scf.py) shows this sequence.

Explicit `pseudo_dir` / `orbital_dir` arguments take precedence. If they are
omitted, `AbacusProfile` reads `ABACUS_PP_PATH` / `ABACUS_ORB_PATH`; these are
the package's only asset-directory environment defaults.

`Abacus` runs one engine calculation for each ASE property evaluation that
requires a calculation. ASE owns optimization, molecular dynamics and NEB
algorithms. `AbacusSocketIO` reuses one engine process for position updates
with a fixed cell and electronic settings. It provides energy and can request
forces/stress independently. See the [socket example](../examples/socketio.py);
it needs a socket-capable engine and is not supported by the tested LTS build.

Calculators choose their output reader from the configured executable's
actual version. LTS v3.10.x selects `legacyio`; the tested develop v3.11 format
uses `latestio`. Each calculator retains its own choice, so a second calculator
cannot change the first one's reader. Use separate directories for separate
calculations. Supported snapshots and validation limits are recorded in the
[compatibility guide](compatibility-ci.md#develop-and-lts-engine-coverage).

## Run the examples

The scripts live in the source checkout and sdist, not the runtime wheel.
From the repository root, with the package installed:

```bash
export ABACUS_COMMAND='mpirun -np 2 abacus'
export ABACUS_PP_ORB=/absolute/path/to/ABACUS/tests/PP_ORB
export OMP_NUM_THREADS=1
python examples/scf.py
```

All eleven scripts read `ABACUS_PP_ORB` and accept `ABACUS_COMMAND` to override
their MPI launcher default (`abacus` from `PATH`). The library takes directory
settings through `AbacusProfile`; `ABACUS_PP_ORB` is a single-directory
convention of the examples. Install ABACUS separately; ASE remains unpatched.

Recent develop builds may name the executable `abacus_basic_para` (or another
feature/parallel variant). Set `ABACUS_COMMAND` to the actual binary; a bare
`abacus` is only correct when that name is on `PATH`.

The SCF example requires `Si_ONCV_PBE-1.0.upf` and
`Si_gga_8au_100Ry_2s2p1d.orb` in the asset directory. Other examples name their
own assets. The directory can be your own collection or ABACUS `tests/PP_ORB`.
Check each script's parameters against your engine build: for example,
`scf.py` selects `genelpa`, which needs ELPA support; use an available solver
such as `scalapack_gvx` when adapting it for an appropriate MPI build.

Each example uses calculation directories named for that example. Several
scripts delete their calculation directories on completion, and the
socket example also clears its named directories before use. Use a dedicated
copy and adjust cleanup if you need retained results. Metadynamics additionally
requires a working PLUMED installation. The examples illustrate usage; validate
scientific settings for your system.

| Example | Purpose | Notes |
| --- | --- | --- |
| [scf.py](../examples/scf.py) | SCF calculation of silicon | `genelpa`; Si assets |
| [relax.py](../examples/relax.py) | Atomic position relaxation | `genelpa`; Si assets |
| [cellrelax.py](../examples/cellrelax.py) | Cell relaxation | `genelpa`; Si assets |
| [bandstructure.py](../examples/bandstructure.py) | Band structure | Band-capable output |
| [dos.py](../examples/dos.py) | Density of states | DOS output |
| [md.py](../examples/md.py) | Molecular dynamics | ASE-driven MD |
| [constraintmd.py](../examples/constraintmd.py) | Constrained molecular dynamics | `nspin=2` |
| [metadynamics.py](../examples/metadynamics.py) | Metadynamics | Requires PLUMED |
| [neb.py](../examples/neb.py) | Nudged elastic band | ASE NEB |
| [soc.py](../examples/soc.py) | Noncollinear spin-orbit coupling | `nspin=4`; SOC support |
| [socketio.py](../examples/socketio.py) | Fixed-cell socket calculations and FileIO comparison | Socket-capable engine |

Start with SCF, then relaxation or MD before adapting the more specialized
examples. Choose numerical settings and convergence criteria for your system.

## Read files without an engine

General input functions return dictionaries describing the supplied files:

```python
from abacuslite.io.generalio import read_input, read_stru

parameters = read_input("INPUT")
structure = read_stru("STRU")
```

For completed outputs, choose the reader for the producing engine. For example,
to read a legacy native-MD trajectory:

```python
from pathlib import Path
from abacuslite.io import legacyio

frames = legacyio.read_abacus_out(Path("OUT.ABACUS/running_md.log"))
energy = frames[-1].get_potential_energy()
```

Use `latestio.read_abacus_out` with a `Path` for newer-format outputs. Keep
companion files together: newer output uses `eig_occ.txt`, and native-MD
geometry normally comes from `MD_dump`. Complete historical legacy MD logs
remain readable without a dump; incomplete trajectories and malformed existing
dumps fail explicitly. Reading preserves source files, including `eig_occ.txt`.
The [migration guide](migration.md) explains compatibility changes, and the
[module reference](reference.md) describes the reader modules.

If you are unsure which reader to use, check the ABACUS version banner in the
running log: 3.10.x LTS uses `legacyio`; the tested develop 3.11 format uses
`latestio`. A configured `Abacus` calculator makes this choice automatically
from the engine version.
