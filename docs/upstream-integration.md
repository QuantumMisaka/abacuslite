# ABACUS and ATST integration audit

This audit records the source comparison performed when the independent
package was created. The maintained package is now version 1.1.0, published
on PyPI; later changes and validation are recorded in
[CHANGELOG.md](../CHANGELOG.md) and the
[compatibility guide](compatibility-ci.md).

Refs fetched on 2026-10-16:

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
a linked abacuslite compatibility change. ATST owns workflow and launcher policy.
While upstream migration is pending, record necessary backports by source
commit and behavior; neither automatically overwrite another repository nor
maintain an untracked alternative implementation.

## Architecture and portability follow-up

The source/API comparison and caller migration steps are recorded in
[the migration guide](migration.md). The 2026-10-17 follow-up retained all
runtime modules and public signatures. It corrected the examples' inherited
ABACUS-relative asset paths: all 11 now accept an explicit asset directory
and engine command. The new startup regression failed on all 11 originals
and passed after the correction, without executing a calculation.

Validation for this follow-up used installed wheels outside the checkout:
Python 3.10 / ASE 3.28 and Python 3.12 / ASE 3.29 each passed 112 tests with
15 skips. Rebuilding from the sdist, reinstalling that wheel and running the
sdist's tests/examples also passed 112 tests with 15 skips on the minimum
environment. Both distributions passed strict Twine metadata checks. The skips
cover nine opt-in engine tests, four separately run consumer tests and two
retained upstream placeholders. Independent review found no blocking issue.
