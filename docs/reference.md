# Module and output-format reference

This reference describes runtime modules and output formats. Setup, test
commands and package verification live in [CONTRIBUTING.md](../CONTRIBUTING.md);
calculator usage and examples are in [the usage guide](usage.md).

## Public API

The [public API contract](public-api.md) defines supported calculator, pure-I/O,
selected running-log and k-point entry points, result semantics, historical
compatibility helpers and change rules. That document is the canonical caller
contract. The format tables below describe the implementation's input formats;
they do not make every internal parser helper public.

## Runtime modules

Runtime code lives under `src/abacuslite`; examples and tests are separate.
Public imports remain `abacuslite`, `abacuslite.io` and `abacuslite.utils`.

See [From ase-abacus to abacuslite](ase-interface.md) for the differences from
the old ASE fork and the current write -> execute -> read lifecycle.

| Runtime module | Responsibility |
| --- | --- |
| `core.py` | `AbacusProfile`, `AbacusTemplate`, ASE `Abacus` and `AbacusSocketIO` |
| `io/generalio.py` | INPUT, STRU and KPT reading/writing |
| `io/legacyio.py`, `io/latestio.py` | Readers for the two existing ABACUS output formats |
| `utils/ksampling.py` | K-point paths and sampling helpers |

ASE owns optimization/MD/NEB algorithms; ATST owns its workflow and launcher
policy. Neither ATST nor Forge is a runtime dependency of this package.
[Package boundaries](design.md) define this separation. The
[integration audit](upstream-integration.md) records preserved ABACUS
features, integrated ATST fixes and reader-instance isolation.

## core.py

This file contains the implementation of the Atomic Simulation Environment (ASE) calculator.

`Abacus.restart` recovers pseudopotentials, orbitals and k-points from an
existing directory: the STRU name comes from INPUT `stru_file`, and KPT is read
only when the input cannot sample k-points implicitly. `Abacus.fixed_density`
reuses the source calculation's charge density from `OUT.<suffix>` and honors an
explicit `read_file_dir`. Both accept `inp=` overrides.

## io

This directory contains the input/output (I/O) functions for extracting information from ABACUS dumped files. A summary is here:

### Long-term-support (LTS) version

The table describes legacy running-log fields. For native MD, `legacyio`
prefers `MD_dump` for complete physical geometry; complete historical log-only
trajectories remain supported. See [output reading](usage.md#read-files-without-an-engine)
for companion-file requirements.

|Item|Regular expression|Example|
|----|----|----|
|esolver_type|'The esolver type has been set to : (\S+)'|`The esolver type has been set to : ksdft_pw`|
|nspin|'nspin\s+=\s+(\d+)'|`nspin = 4`|
|number of bands|'NBANDS\s+=\s+(\d+)'|`NBANDS = 40`|
|number of atoms|'TOTAL ATOM NUMBER\s*=\s*(\d+)'|`TOTAL ATOM NUMBER = 2`|
|lattice constant|'lattice constant \(Angstrom\)\s*=\s*(-?\d+(\.\d+)?)'|`lattice constant (Angstrom) = 0.529177`|
|lattice vectors|'^Lattice vectors: \(Cartesian coordinate: in unit of a_0\)$'|` Lattice vectors: (Cartesian coordinate: in unit of a_0)`|
|coordinate system|'^(DIRECT\|CARTESIAN) COORDINATES'|`DIRECT COORDINATES`|
|atomic positions|'^tau[c\|d]_([A-Z][a-z]?)\d+\s+(-?\d+(\.\d+)?)\s+(-?\d+(\.\d+)?)\s+(-?\d+(\.\d+)?)*'|`taud_As1            0.2500000000        0.2500000000        0.2500000000  1.7321        0.0000000000        0.0000000000        0.0000000000`|
|eigenvalues|'\d+/\d+\s+kpoint\s+\(Cartesian\)\s+=\s+(-?\d(\.\d+)?(e-\d+)?)\s+(-?\d(\.\d+)?(e-\d+)?)\s+(-?\d(\.\d+)?(e-\d\|+)?)\s+\(\d+\s+pws\)'|` 1/1 kpoint (Cartesian) = 0.0000 0.0000 0.0000 (230 pws)`|
|atomic forces|'\s\*TOTAL\-FORCE\s\*\(eV\s*/Angstrom\)'|` TOTAL-FORCE (eV/Angstrom)     `|
|total stress|'\s\*TOTAL\-STRESS\s\*\(KBAR\)'|` TOTAL-STRESS (KBAR)          `|
|kpoints and weights|'\s\*(IBZ\|KPOINTS)\s+(DIRECT\|CARTESIAN)_X\s+(DIRECT\|CARTESIAN)_Y\s+(DIRECT\|CARTESIAN)_Z\s+WEIGHT(\s+ibz2bz)?'|` KPOINTS    DIRECT_X    DIRECT_Y    DIRECT_Z  WEIGHT`|
|energy|'\s*ENERGY\s+Rydberg\s+eV'|`     Energy           Rydberg                 eV      `|
|total magnetism|'\s\*Total\sMagnetism\s\(uB\)(\s+x\s+y\s+z)?\s\*'|` Total Magnetism (uB)    `|   

### Latest version

|Item|Regular expression|Example|Notes|
|----|----|----|----|
|esolver_type|'#ENERGY SOLVER#\s+(\S+)'|` #ENERGY SOLVER# ksdft_pw`||
|nspin|'nspin\s+=\s+(\d+)'|`nspin = 4`||
|number of bands|||has been removed|
|number of atoms|'TOTAL ATOM NUMBER\s*=\s*(\d+)'|`TOTAL ATOM NUMBER = 2`||
|lattice constant|'lattice constant \(Angstrom\)\s*=\s*(-?\d+(\.\d+)?)'|`lattice constant (Angstrom) = 0.529177`||
|lattice vectors|'^Lattice vectors: \(Cartesian coordinate: in unit of a_0\)$'|` Lattice vectors: (Cartesian coordinate: in unit of a_0)`||
|coordinate system|'^(DIRECT\|CARTESIAN) COORDINATES'|`DIRECT COORDINATES`||
|atomic positions|'atom\s+x\s+y\s+z\s+mag‘|` atom                  x                  y                  z     mag`|"tauc/taud" suffix has been removed, therefore the way to read the coordinates changes to find the head of the table, then read the following `number of atoms` lines. On the other hand, if the `calculation` is set to `md`, ABACUS will not dump the atomic positions to running log anymore, instead, will read from the MD_dump file|
|eigenvalues|'spin=(\d)\s+k-point=(\d+)/(\d+)\s+Cartesian=\s*(-?\d(\.\d+)?(e-\d+)?)\s+(-?\d(\.\d+)?(e-\d+)?)\s+(-?\d(\.\d\|+)?(e-\d+)?)\s+\(\d+\s+plane wave\)'|  spin=1 k-point=1/1 Cartesian=0.0000000 0.0000000 0.0000000 (1837 plane wave)|eigenvalues information has been removed from the running log, the file istate.info is renamed as eig_occ.txt, where the eigenvalues are read|
|atomic forces|'#\s\*TOTAL\-FORCE\s*\(eV\s*/Angstrom\)\s\*#'|`  #TOTAL-FORCE (eV/Angstrom)#`||
|total stress|'#\s\*TOTAL\-STRESS\s*\(kbar\)\s\*#'|` #TOTAL-STRESS (kbar)#    `||
|kpoints and weights|'\s*(IBZ\|KPOINTS)\s+(DIRECT\|CARTESIAN)_X\s+(DIRECT\|CARTESIAN)_Y\s+(DIRECT\|CARTESIAN)_Z\s+WEIGHT(\s+ibz2bz)?'|` KPOINTS    DIRECT_X    DIRECT_Y    DIRECT_Z  WEIGHT`||
|energy|'\s*ENERGY\s+Rydberg\s+eV'|`     Energy           Rydberg                 eV      `||
|total magnetism|'\s\*Total\sMagnetism\s\(uB\)(\s+x\s+y\s+z)?\s\*'|` Total Magnetism (uB)    `||

Please look at detailed implementations in the following files.

### generalio.py

This module contains the general I/O functions for ABACUS.

`write_stru` writes the ASE mass of each species, including isotope masses set on
the `Atoms` object, and rejects different masses within one species before
creating the file.

### latestio.py

This module contains the I/O functions for the latest version of ABACUS.

### legacyio.py

This module contains the I/O functions for the Long-Term-Support (LTS) version of ABACUS.

## utils

This directory contains the utility modules for Abacuslite.

### ksampling.py

This module contains the wrapper of k-point sampling functions and helper functions.

## xtest.sh

This compatibility launcher runs the extracted offline tests. From the repository
root use `bash src/abacuslite/xtest.sh`, or use `python -m pytest tests/unit -q`
directly. Tests are no longer embedded in the runtime source files. The launcher
is a source-checkout convenience, not an installed console entry point.

## Energy metadata (1.2.1)

Both file readers keep `energy` and force-consistent `free_energy` equal to
ABACUS `E_KohnSham`, which already includes the printed `E_entropy(-TS)` term.
When that term is present, `Atoms.info["energy_without_entropy"]` contains
`E_KohnSham - E_entropy(-TS)` in eV. The file-backed `Abacus` calculator
forwards it in `calc.results["energy_without_entropy"]` from the selected frame.
It is not a standard ASE property or a replacement for `free_energy`; absent
entropy means absent metadata. The socket contract is unchanged.
