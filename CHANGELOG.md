# Changelog

## 1.1.0rc1 — unreleased candidate

- Establish an independent source package from ABACUS develop `4b92455ca`,
  retaining original attribution, module paths and socket support.
- Integrate ATST SCF structure-frame matching, periodic equivalence and atom
  mapping validation, actual STRU filename handling, and Fermi-level retention.
- Correct decimal point-KPT parsing and tolerate absent Fermi levels.
- Normalize Cartesian log coordinates by the lattice constant when matching
  SCF frames to STRU, for both output readers.
- Keep the upstream read-only `eig_occ.txt` behavior: repeated collection no
  longer consumes the input file. This intentionally differs from old ATST.
- Isolate each calculator's output-format selection; compatibility switch
  calls affect new bare templates only, not existing calculator instances.
- Add persistent installed ATST/Forge consumer CI, bidirectional reader
  isolation regressions and a cross-repository compatibility guide.
- Separate offline tests from opt-in engine tests and package source fixtures.
- Raise the ASE dependency floor to 3.28 for the supported candidate matrix;
  this release does not claim the old unverified `ase>=3.22` range.

This candidate is not a PyPI publication or a complete engine compatibility
certification. Existing consumers must validate their installed integration
before removing vendored implementations or changing production dependencies.
