# ABACUS and ATST integration audit

The maintainer confirmed the independent package version `1.1.0rc1` on
2026-10-16. It remains an unreleased candidate.

Refs fetched on that date:

- ABACUS develop: `4b92455cab1b1a51e8534b7eb869798ae1241b1b`.
- ATST main: `45d8c78de8a605c127cd4c36742d0c9525a0a6b6`.
- Independent package baseline: `f36f3664edd8fe39719b1237f54eb0c9da482680`.

Production functions and methods were compared structurally after excluding
embedded tests/docstrings. Every substantive difference was inspected against
ATST's `PATCHES.md`. This audit found no missing registered general fix; it is
not an assertion that untested behavior is correct. Do not freeze function
hashes as the long-term compatibility gate.

| Capability / difference | Disposition in independent package | Behavior evidence |
| --- | --- | --- |
| Socket calculator, fixed cell, property metadata and reorder | Preserve newer ABACUS implementation | `test_core.py` socket tests |
| Version parsing and engine failure diagnostics | Preserve newer ABACUS implementation | Version tests; real engine failures still need integration coverage |
| STRU `LATTICE_PARAMETER` | Preserve newer ABACUS implementation | `test_read_stru_with_lattice_parameter` |
| Tolerant legacy band reader | Use current ABACUS implementation, which supersedes ATST's old patch | Legacy band fixtures in `test_legacyio.py` |
| Missing Fermi level in both readers | Port ATST tolerance | `test_reader_contract.py` |
| Calculator `efermi` retention | Port ATST result projection | `test_consumer_contract.py`; installed ATST/ASE force request |
| SCF current-structure frame / PBC / mapping / malformed frame / custom STRU | Port ATST semantics | `test_frame_selection.py` |
| Point-KPT decimal coordinates and weights | Port ATST regex correction | `test_point_kpt_preserves_fractional_coordinates_and_weights` |
| `eig_occ.txt` lifecycle | Preserve ABACUS read-only behavior; supersede ATST deletion | Repeated latest-reader test |
| Reader isolation | Independent package repair | Two creation orders, alternate reads, compatibility-switch changes |
| Cartesian log length unit | Independent package repair | Non-unit lattice constant, both readers |
| ATST launcher/version-command policy | Remains in ATST's profile adapter | Installed consumer test uses the real `ATSTAbacusProfile` |

Original source and test attribution: [UPSTREAM.md](../UPSTREAM.md). General
ATST fixed-density discovery, native version probing and backup suffix tests
are also retained in `tests/unit/test_consumer_contract.py`; duplicate tests
already covered by current upstream tests were not copied again.

## What instance isolation means

An `Abacus` calculator chooses its reader from its own profile version at
construction and keeps that choice in its own template. A second calculator
cannot change the first calculator's reader. For example, a 3.10 calculator
and a 3.11 calculator can alternate parsing their respective output formats
in one Python process.

`switch_io_backend_version()` remains a compatibility default for newly created
bare `AbacusTemplate` objects. It does not reconfigure existing objects or
explicit-profile calculators. Direct `legacyio` / `latestio` functions remain
available for output-only consumers.

This is reader-selection isolation. It does not make simultaneous calculations
in the same directory safe, make a single calculator thread-safe, or certify
all ABACUS versions.

## Keeping sources convergent

General parser/calculator fixes should become tests and fixes here. Engine
format changes belong in ABACUS and should carry a minimal output fixture and
a linked plugin compatibility change. ATST owns workflow and launcher policy.
While upstream migration is pending, record necessary backports by source
commit and behavior; neither automatically overwrite another repository nor
maintain an untracked alternative implementation.
