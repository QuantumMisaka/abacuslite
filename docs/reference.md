# Module and output-format reference

Setup and verification live in [Contributing](../CONTRIBUTING.md). Calculator
arguments and result semantics are defined by the [public API](public-api.md);
usage examples are in [Usage](usage.md).

## Runtime modules

| Module | Responsibility |
| --- | --- |
| `core.py` | ABACUS profile, file-backed calculator and socket calculator |
| `io/generalio.py` | INPUT, STRU and KPT reading and writing |
| `io/legacyio.py` | ABACUS 3.10.x LTS running log and native-MD output |
| `io/latestio.py` | Tested develop running log, band data and native-MD output |
| `utils/ksampling.py` | K-point paths and sampling helpers |

ASE owns optimization, MD and NEB algorithms. This package owns the calculator
and parser. ATST and Forge own their workflow and launcher policies. See
[Package design](design.md) for repository boundaries.

## File formats

- **INPUT:** key/value settings consumed by the ABACUS engine.
- **STRU:** species and atom records, coordinate type, lattice constant and
  lattice vectors. Atom records begin with three coordinates and may contain
  mobility flags (`m`), velocity (`v`, `vel`, or `velocity`), a scalar or
  three-component Cartesian magnetic moment (`mag` or `magmom`), or a
  spherical moment with `angle1` and `angle2`. Each keyword accepts exactly
  its defined number of values. Malformed or duplicate fields raise
  `ValueError`; line spacing does not determine the field count.
- **KPT:** Monkhorst-Pack sampling or explicit point meshes. Line-mode writing
  is not implemented.

The STRU reader returns file-native values: lattice constants are in Bohr and
coordinates follow the declared coordinate type. The writer emits ASE species
masses and velocities in ABACUS units; it rejects different masses within one
species because a single species record cannot represent them.

## Output readers

Both readers return ASE `Atoms` objects with available single-point results.
They accept a path or caller-owned text stream with a filesystem name; that name
is used to locate companion files. Streams without a filesystem name are not
supported, and caller streams remain open.

Latest-format eigenvalues and occupations come from `eig_occ.txt`. Native MD
uses `MD_dump` when present. Its positions are Cartesian Angstrom values and
its lattice vectors are in alat units. Legacy native MD accepts complete
`running_md.log` trajectories and prefers `MD_dump` when available. Parsed
frames have periodic boundaries enabled in all directions; source geometry
coordinates still follow the relevant output format. See [output reading](usage.md#read-files-without-an-engine)
and the [public API](public-api.md) for companion-file and result details.

All readers preserve source files and support repeatable reads. Missing or
malformed output raises an error instead of inventing forces, stress, energies
or magnetic properties.

## Energy convention

File readers expose `energy` and `free_energy` as ABACUS `E_KohnSham`, the
force-consistent energy including the printed entropy term. When available,
`Atoms.info["energy_without_entropy"]` stores `E_KohnSham - E_entropy(-TS)`.
The file-backed calculator forwards that value as optional
`calc.results["energy_without_entropy"]`; absent entropy remains unknown.
