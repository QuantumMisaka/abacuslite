# Public API and compatibility contract

This is the plugin-owned contract for callers and external compatibility tests.
It applies to the supported engine snapshots in [supported versions](supported-versions.md).
The package version, engine version and socket schema version are independent.
Repository hosting and maintenance membership do not change this boundary.

## Supported entry points

### Calculators and profiles

Import `Abacus`, `AbacusProfile` and `AbacusSocketIO` from `abacuslite`.

- `AbacusProfile(command, pseudo_dir=None, orbital_dir=None,
  omp_num_threads=None, **kwargs)` describes the executable and asset directories.
  `version()` runs the configured command with `--version` and returns the
  engine's version string; `parse_version(stdout)` accepts ABACUS output with
  launcher preamble and raises `RuntimeError` when no version can be found.
  Only omitted directories fall back to `ABACUS_PP_PATH`/`ABACUS_ORB_PATH`;
  explicit empty strings are preserved. `inp` directory overrides take
  precedence over the profile.
- `Abacus(profile=None, directory='.', **kwargs)` accepts explicit
  `pseudopotentials`, `basissets`, `kpts` and ABACUS parameters under `inp`.
  Construction probes the engine version. Call through ASE's calculator/Atoms
  API, including energy, force and stress requests. `write_input(atoms,
  properties=None, system_changes=None)` prepares inputs without running an
  SCF calculation, but construction still requires a usable profile.
- `Abacus.restart(profile=None, directory='.', **kwargs)` reconstructs a
  calculator from INPUT and its selected STRU/KPT; it is not a completed-output
  reader. `fixed_density(kpts, symmetry='off', profile=None, **kwargs)` creates
  an NSCF calculator using the source output suffix unless `read_file_dir` is
  supplied. `band_structure(efermi=None)` returns an ASE `BandStructure`.
- `AbacusSocketIO` accepts the documented profile/directory, socket endpoint,
  timeout and input options. Use ASE property requests or `calculate`, and
  `close()` or the context manager for lifecycle management. The cell and
  input parameters remain fixed within a session. See the
  [socket contract](socket-contract.md) for supported properties, metadata and
  rejection behavior.

`AbacusProfile.version()` and its ASE `BaseProfile.run(directory, inputfile,
outputfile, errorfile=None, append=False)` launcher hook may be overridden by
adapters. Launcher policy belongs to the adapter; parser selection and result
assembly remain in this package.

Each calculator keeps the format selected from its own profile. Constructing
or running another calculator must not change the first calculator's results.
Inspect the engine through `profile.version()`; do not inspect a template,
module-global switch, server object or child-process handle.

### Results and frame selection

After a successful file-backed evaluation, `calc.results` exposes available
quantities with the following semantics:

| Quantity | Representation |
| --- | --- |
| `energy`, `free_energy` | eV; both equal ABACUS `E_KohnSham`, including its printed entropy contribution |
| `forces` | `(natoms, 3)`, eV/Angstrom, in the caller's atom order |
| `stress` | ASE Voigt order `(xx, yy, zz, yz, xz, xy)`, eV/Angstrom^3, with ASE's sign convention |
| `efermi`, `fermi_level` | eV aliases when a Fermi level is available; absence is not zero |
| `magmoms` | Bohr magnetons, `(natoms,)` for collinear or `(natoms, 3)` for noncollinear output |
| `energy_without_entropy` | Optional eV metadata: `E_KohnSham - E_entropy(-TS)`; absent if the entropy term is absent |
| `eigenvalues`, `occupations` | Available band arrays in `(nspins, nkpts, nbands)` order; eigenvalues in eV |

Noncollinear result projection needs no caller changes to ASE's global
property definitions (fixed in 1.2.2). The vector
`magmoms` value is available in `results`; this does not expand ASE's
`Properties` schema or promise that every ASE magnetic-property method accepts
vector moments.

SCF collection matches the written STRU, including periodic equivalence, rather
than selecting an unrelated last trial frame. It uses an absolute `1e-4`
Angstrom tolerance for cell components and periodic position residuals, with
no relative tolerance. That bound covers the six-significant-digit lattice
header written to running logs: the half-ulp is up to `5e-5` Angstrom for
components in `[10, 100)` Angstrom, so a smaller default could not match a
rounded but correct cell. Malformed or unmatched structure handoffs raise
`RuntimeError`. Native relaxation/MD collection selects the final frame.
The reader does not consume `abacus.json`; the running log alone identifies
the SCF frame.
File-backed results restore the caller's atom ordering after species grouping.

Missing force/stress data is not replaced with fabricated zero arrays. ASE
property access can raise `PropertyNotImplementedError` when unavailable.
Historical raw readers supply zero initial magnetic moments when no magnetic
table exists; these zeros alone are not evidence of a calculated magnetization.

### Pure input/output

The functions below work without constructing a calculator or launching ABACUS.
Input file paths accept `str` or `pathlib.Path`.

| Entry in `abacuslite.io.generalio` | Arguments and result |
| --- | --- |
| `read_input(fn)` | Mapping of INPUT keys to string values |
| `write_input(data, fn)` | Write INPUT and return its path |
| `read_stru(fn)` | Mapping with `lat`, `coord_type`, `species`; species include symbols, masses, file references and atom records |
| `write_stru(stru, outdir, pp_file, orb_file=None, fname='STRU')` | Write ASE `Atoms` in species order and return its path; preserve species masses and explicit velocities |
| `read_kpt(fn)` | Sampling mapping: `mode` and mode-specific mesh, shifts or explicit points |
| `write_kpt(data, fn)` | Write a `mp-sampling` or `point` mapping and return its path; line-mode writing is not implemented |

STRU dictionaries retain file-native coordinates and lattice conventions;
`lat.const` is in Bohr. They are not an ASE `Atoms` replacement. STRU cannot
represent different masses within one chemical species: `write_stru` raises
`ValueError` before writing that file.

Both `abacuslite.io.latestio` and `abacuslite.io.legacyio` expose:

```python
read_abacus_out(fileobj, index=slice(None), results_required=True,
                sort_atoms_with=None)
```

Use a `pathlib.Path` to the running log in both formats. The latest reader
requires it to locate companion files; the legacy reader additionally retains
support for string paths and text file handles. An integer index returns one ASE `Atoms`;
a slice returns a list. The default returns all available frames.
`sort_atoms_with` is a full permutation of output atom indices, applied to
atoms, forces and magnetic moments. Callers must supply a valid permutation.
`results_required` is retained but currently has no effect.

Parsing is read-only and repeatable, including `eig_occ.txt`; no file is
consumed. Latest-format output requires its companion band file. Native MD
uses `MD_dump` for physical Angstrom geometry and PBC; the legacy reader can
also read a complete log-only trajectory. Raw non-MD readers retain legacy
log-coordinate conventions and do not guarantee normalized Cartesian geometry
or PBC. The file-backed calculator performs its own structure normalization
and matching; do not infer a universal geometry contract from raw-reader `Atoms`.

Parsed single-point calculators expose available ASE energy, force, stress,
Fermi and band getters. Optional no-entropy metadata is in
`Atoms.info["energy_without_entropy"]`. Absent Fermi data yields `None` from
the parsed calculator's `get_fermi_level()`.

### Selected running-log fields

ATST and Forge also consume partial logs that need not have the companions
required by `read_abacus_out`. The following names are supported in **both**
`legacyio` and `latestio`; consumers need not depend on their implementation
sharing:

| Function | Result |
| --- | --- |
| `read_energies_from_running_log(src)` | `(rydberg_tables, ev_tables)`, each a list of dictionaries with the printed `E_*` keys |
| `read_forces_from_running_log(src)` | List of `(natoms, 3)` arrays in output atom order, eV/Angstrom |
| `read_stress_from_running_log(src)` | List of `(3, 3)` tensors, eV/Angstrom^3 with ASE sign, already converted from ABACUS kbar |
| `read_iter_header_from_running_log(src)` | List of `(ionic_step, electronic_step)` integer pairs |
| `find_final_info_with_iter_header(info, headers)` | Select the final electronic-iteration entry for each ionic step from aligned, nonempty lists |

`src` accepts a path (`str`/`Path`) or a list of log lines. No recognized
tables returns empty lists (energy returns `([], [])`); a partially written
log may yield only complete tables. These functions do not establish
convergence, complete trajectory geometry or successful engine execution.
The caller owns those judgments. Missing files raise `FileNotFoundError`;
malformed content may raise `ValueError`, `AssertionError`, `KeyError` or
`IndexError`. There is no promised exception message text or universal
malformed-output exception type in 1.x.

### K-point helpers

The supported names in `abacuslite.utils.ksampling` are
`convert_kspacing_to_kpts`, `get_kpath`, `interpolate_kpath`, `merge_ksgm`,
`make_kstring`, `make_klines` and `kpathgen`, with their documented arguments.
`kpathgen(atoms)` returns `(path_string, special_points)` for ASE `bandpath`.
The existing helper tests cover interpolation, path breaks and sampling;
exact symmetry paths can depend on the declared seekpath/spglib versions.

## Compatibility and internal implementation

The names and behavior above are the supported surface. New optional results
and compatible entry points may be added in minor releases. Fixes that restore
documented units, ordering or scientific meaning may ship in patch releases,
with a changelog and affected regression evidence. Removal, renaming or an
incompatible change to a supported signature/result requires a major release,
an explicit migration path and a documented deprecation in a preceding minor
release. Do not use a version pin as a substitute for a public contract.

`load_pseudo`, `load_orbital`, `file_safe_backup`, `AbacusTemplate` and
`switch_io_backend_version` remain importable historical compatibility
helpers. No exports are removed by this clarification. Existing users should
migrate asset selection to explicit mappings and use calculator/profile or
explicit reader entry points; removal of these named helpers also requires
the documented deprecation/migration process. Their discovery heuristics and
internal object layouts are not new stable extension points.

Other implementation helpers, wildcard-import leakage, `_legacyio`,
`__LEGACYIO__`, template attributes and ASE server/process internals are not
public plugin contracts. An internal refactor may change them while all
supported behavior remains unchanged.

## Verification responsibilities

`tests/unit/test_public_api.py` exercises actual input writers, parsers and
calculator handoffs through public calls; only the external executable is
replayed. It runs with the installed wheel and the sdist-rebuilt wheel in
the ordinary package matrix. Existing focused unit/consumer tests cover
additional edge cases. These offline checks do not certify an engine build.

ABACUS retains real-engine tests against literal raw energy/force/stress,
band and magnetic tables and native-MD geometry. Its test harness must not use
the plugin parser to generate its own expected values, inspect private reader
state or mutate ASE's global registries. A compatibility claim identifies the
engine revision, plugin artifact, harness revision and case results.
Both repositories' tests are needed when output formats or socket behavior
change. See [compatibility and CI](compatibility-ci.md).
