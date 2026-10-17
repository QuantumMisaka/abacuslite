# Using abacuslite

Install the package following the [README](../README.md#installation).
The runtime depends on ASE, NumPy and seekpath. Tested package combinations
include Python 3.10 / ASE 3.28 and Python 3.12 / ASE 3.29; the declared
dependency range is not a guarantee for every future combination.

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
their launcher default. The library itself takes these settings through
`AbacusProfile`; these environment variables are a convention of the examples.
ABACUS is not downloaded automatically and ASE is not patched during install.

The SCF example requires `Si_ONCV_PBE-1.0.upf` and
`Si_gga_8au_100Ry_2s2p1d.orb` in the asset directory. Other examples name their
own assets. The directory can be your own collection or ABACUS `tests/PP_ORB`.
Check each script's parameters against your engine build: for example,
`scf.py` selects `genelpa`, which needs ELPA support; use an available solver
such as `scalapack_gvx` when adapting it for an appropriate MPI build.

Several scripts delete their calculation directories on completion, and the
socket example also clears its named directories before use. Use a dedicated
copy and adjust cleanup if you need retained results. Metadynamics additionally
requires a working PLUMED installation. Example startup tests check imports and
configuration; they do not certify complete scientific workflows.

| Example | Purpose |
| --- | --- |
| [scf.py](../examples/scf.py) | SCF calculation of silicon |
| [relax.py](../examples/relax.py) | Atomic position relaxation |
| [cellrelax.py](../examples/cellrelax.py) | Cell relaxation |
| [bandstructure.py](../examples/bandstructure.py) | Band structure |
| [dos.py](../examples/dos.py) | Density of states |
| [md.py](../examples/md.py) | Molecular dynamics |
| [constraintmd.py](../examples/constraintmd.py) | Constrained molecular dynamics |
| [metadynamics.py](../examples/metadynamics.py) | Metadynamics with PLUMED |
| [neb.py](../examples/neb.py) | Nudged elastic band |
| [soc.py](../examples/soc.py) | Noncollinear spin-orbit coupling |
| [socketio.py](../examples/socketio.py) | Fixed-cell socket calculations and FileIO comparison |

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
