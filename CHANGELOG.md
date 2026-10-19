# Changelog

## Unreleased

### Fixed

- Report `free_energy = E_KohnSham - E_entropy(-TS)` and keep
  `energy = E_KohnSham`. This preserves the force-consistent energy required
  by FCP v2 and ATST constant-potential calculations on smeared systems.

## 1.2.0

Published on [PyPI](https://pypi.org/project/abacuslite/1.2.0/) on
2026-10-19 (UTC+08:00).

### Added

- Default `pseudo_dir` and `orbital_dir` to `ABACUS_PP_PATH` and
  `ABACUS_ORB_PATH` when the profile arguments are omitted (`None`); explicit
  values, including an empty string, are preserved. These are the package's
  only asset-directory environment defaults.

### Fixed

- Write ASE atom masses to STRU for each chemical species, including isotope
  masses; reject different masses within one species before creating the file.
- Resolve fixed-density charge input from the source calculation's output
  suffix, while retaining an explicitly supplied `read_file_dir`.
- Restart from the STRU filename selected by INPUT and read KPT only when
  needed. Explicit k-points and implicit gamma/kspacing sampling no longer
  require a KPT file; other missing KPT files still fail.

## 1.1.0

Published on [PyPI](https://pypi.org/project/abacuslite/1.1.0/) on
2026-10-18 (UTC+08:00).

- Provide the independent ASE plugin as a wheel and source distribution with
  unchanged public imports. Preserve the validated runtime from the final
  candidate; the stable release adds packaging, documentation and release gates.

- Honor explicit engine/consumer pytest markers and reject unknown markers or
  configuration keys; offline tests no longer depend on checkout directory or
  function names. Validate wheel and sdist tests outside the checkout, and
  include the source-only test launchers in the sdist.
- Restore the skipped pseudopotential/orbital filename-selection tests with
  self-contained temporary assets, without requiring an ABACUS installation.
- Give cell relaxation, DOS and metadynamics examples separate calculation
  directories, and use the standard `abacus` command in the NEB default launcher.
  Check default and overridden example settings before engine execution.
- Preserve explicit ASE atomic velocities in STRU, converting from Angstrom
  per ASE time unit to Bohr per atomic time unit and maintaining species order;
  atoms without velocities retain the existing zero initialization.
- Prefer `MD_dump` for LTS native MD geometry; retain complete single-file
  `running_md.log` trajectories when no dump exists. Assemble physical
  Angstrom coordinates/cells and periodic ASE frames, recognize unpadded LTS
  ionic-step headers, and reject incomplete geometry or malformed dumps
  without changing SCF/relax output semantics.
- Align the default SCF structure-identity tolerance with ATST 2.2.9:
  `1e-5` Angstrom for cell components and periodic Cartesian residuals,
  with `rtol=0`. Explicit `atol` overrides remain supported. The former
  `1e-5` to `1e-4` interval is now rejected rather than silently selecting
  a mismatching SCF frame; native relax/MD last-frame selection is unchanged.
- Establish an independent source package from ABACUS develop `4b92455ca`,
  retaining original attribution, module paths and socket support.
- Integrate ATST SCF structure-frame matching, periodic equivalence and atom
  mapping validation, actual STRU filename handling, and Fermi-level retention.
- Correct decimal point-KPT parsing and tolerate absent Fermi levels.
- Normalize Cartesian log coordinates by the lattice constant when matching
  SCF frames to STRU, for both output readers.
- Convert latest-format native MD `MD_dump` lattice vectors from alat units to
  Angstrom and mark those ASE frames periodic; dump-reader dictionaries and
  their already-Angstrom Cartesian positions retain their existing units.
- Keep the upstream read-only `eig_occ.txt` behavior: repeated collection no
  longer consumes the input file. This intentionally differs from old ATST.
- Isolate each calculator's output-format selection; compatibility switch
  calls affect new bare templates only, not existing calculator instances.
- Add persistent installed ATST/Forge consumer CI, bidirectional reader
  isolation regressions and a cross-repository compatibility guide.
- Make all examples accept explicit engine/asset environment settings and
  document source layout, installation and consumer migration.
- Separate offline tests from opt-in engine tests and package source fixtures.
- Raise the ASE dependency floor to 3.28 for the supported candidate matrix;
  this release does not claim the old unverified `ase>=3.22` range.

Publication status and artifact identities are recorded in the
[release record](docs/superpowers/plans/2026-10-17-1.1.0-release.md).
Existing consumers must validate their installed integration
before removing vendored implementations or changing production dependencies.
