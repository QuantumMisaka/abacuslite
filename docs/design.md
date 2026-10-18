# Independent ASE calculator package

This repository owns the installable ASE calculator and I/O package. ABACUS
retains engine integration tests; ATST and Forge consume this package.

The package preserves `Abacus`, `AbacusProfile`, `AbacusSocketIO`, and the
`abacuslite.io` and `abacuslite.utils` module paths. Keep source layout changes
separate from unrelated API rewrites. Preserve upstream socket support and
diagnostics while carrying the general SCF frame, Fermi-level and point-KPT
corrections.

See [From ase-abacus to abacuslite](ase-interface.md) for the differences from
the old ASE fork and the current lifecycle.

I/O functions are independent of engine execution. Output parsing is read-only
and repeatable. A calculator keeps its reader choice when another calculator is
constructed. Existing reader functions remain available for explicit selection.

## Asset handling

`abacuslite` consumes explicit pseudopotential/orbital directories and file
mappings. `AbacusProfile` falls back to `ABACUS_PP_PATH` and `ABACUS_ORB_PATH`
only when the corresponding argument is omitted; these are the package's only
asset-directory environment defaults. Dataset download, `element.json`
matching, copy/symlink and batch preparation belong to
abacustest/abacusforge.

## Boundaries

ATST owns workflow configuration and launcher policy. Forge owns its native
default, optional parser and fact projection. ABACUS keeps only the engine-side
compatibility harness under `interfaces/ASE_interface`; this package is the
maintained calculator and parser implementation. ABACUS is not a submodule
consumer and does not vendor this source.

Package, engine and output-format versions are distinct. See the
[compatibility record](compatibility-ci.md) for tested snapshots.

Use one source implementation. Existing consumers should migrate direct
vendored imports; compatibility modules should forward to this package rather
than keep a second implementation.

Source provenance is recorded in [UPSTREAM.md](../UPSTREAM.md).
