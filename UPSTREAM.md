# Source provenance

Initial snapshot imported from `deepmodeling/abacus-develop`,
`interfaces/ASE_interface`, commit
`4b92455cab1b1a51e8534b7eb869798ae1241b1b` (2026-10-16).

Original repository: https://github.com/deepmodeling/abacus-develop
Original history: https://github.com/deepmodeling/abacus-develop/commits/4b92455cab1b1a51e8534b7eb869798ae1241b1b/interfaces/ASE_interface

This is a snapshot import; the original Git history is linked, not rewritten
or claimed as newly authored. Original author notices are retained. The root
LICENSE is copied from the same ABACUS commit. ATST adaptations are recorded below with their source and regression evidence.

## Integrated ATST adaptations

Source: https://github.com/QuantumMisaka/atst-tools/tree/45d8c78de8a605c127cd4c36742d0c9525a0a6b6

The SCF frame helpers, template input/result handling, point-KPT reader,
missing-Fermi tolerance, frame-selection regressions and multiframe fixtures
are adapted from `src/atst_tools/external/ASE_interface` and `tests/unit`
at that revision. ATST authorship and its LGPL-3.0-or-later licensing are
acknowledged; the combined distribution retains the ABACUS LGPL-3.0 terms.
The older ATST implementation does not replace the newer ABACUS socket or
execution diagnostics. The upstream non-destructive `eig_occ.txt` reader is
retained, and its repeatability is tested.

The independent package additionally isolates calculator reader selection
from the compatibility global default. Behavioral changes and validation
are recorded in CHANGELOG.md and the implementation plan.

Additional generic fixed-density, native version-probe and backup-suffix
regressions are adapted from ATST `tests/unit/test_abacuslite_profile.py` at
the same revision. The [integration audit](docs/upstream-integration.md) maps
all substantive source differences to retained behavior and test ownership.
