# Installing and migrating to independent abacuslite

The package retains the ABACUS ASE interface design and module
responsibilities. The `src` layout separates installable code from examples and
test assets; consumers still import `abacuslite`.

## Architecture continuity

The ASE inheritance remains `AbacusProfile(BaseProfile)`,
`AbacusTemplate(CalculatorTemplate)`, `Abacus(GenericFileIOCalculator)` and
`AbacusSocketIO(SocketIOCalculator)`. General input I/O, output readers and
K-point helpers remain in their modules. ATST owns workflow and launcher
policy; this package adds no scheduler or service layer.

See [From ase-abacus to abacuslite](ase-interface.md) for the differences from
the old ASE fork and [the integration audit](upstream-integration.md) for
source-level detail.

## Install one implementation

Use a fresh virtual environment, following README.md.
Install a released version from [PyPI](https://pypi.org/project/abacuslite/),
for example `pip install 'abacuslite==1.2.1'` once its publication is complete.
For development use `pip install -e .`.

Do not run consumer validation from a directory containing another top-level
`abacuslite` source tree. In a virtual environment, verify the installed import
from a neutral directory:

```bash
cd /tmp
python - <<'PY'
from importlib.metadata import version
from pathlib import Path
import sys
import abacuslite

location = Path(abacuslite.__file__).resolve()
print(version('abacuslite'), location)
assert location.is_relative_to(Path(sys.prefix).resolve())
PY
```

This check intentionally rejects an editable install; use a built wheel for
consumer acceptance. Editable installs remain appropriate for development.
Verify `python -m pip check` after installing consumer dependencies as well.

## Caller migration

| Existing use | Migration |
| --- | --- |
| `from abacuslite import Abacus, AbacusProfile` | Keep the import and constructor calls; change installation source |
| ABACUS socket calculator | Keep `AbacusSocketIO`; verify the selected engine supports its protocol |
| `abacuslite.io.generalio`, `legacyio`, `latestio` | Keep module paths and explicitly selected reader functions |
| ATST workflow API / CLI | Keep ATST as the workflow entry; verify it selects the installed external package |
| Direct `atst_tools.external.ASE_interface.abacuslite...` import | Migrate to ATST's adapter for calculators/profile policy, or use `abacuslite.io...` for pure I/O |
| Forge collection | Keep the explicit optional parser selection and native default; validate the supported package/Forge pair |
| Running tests from the old production modules | Use `pytest` against `tests/`; fixtures and examples ship in sdist, not the runtime wheel |
| Examples relying on ABACUS's parent-directory layout | Set `ABACUS_PP_ORB` and `ABACUS_COMMAND`; install the package before running |

ATST versions that depend on abacuslite use `abacuslite>=1.1,<2` and thin
forwarding imports. The vendored copy remains only as a frozen audit baseline.
Consumers that import `atst_tools.external.ASE_interface.abacuslite...`
directly should migrate to the installed package; new code should use it
rather than add a second parser or move ATST launcher policy here.

## Intentional compatibility changes

- Python remains 3.10+. The supported dependency floor is ASE 3.28,
  instead of the old unverified 3.22 declaration; NumPy and seekpath have explicit
  bounds in `pyproject.toml`. Check existing environment constraints first.
- Output parsing preserves `eig_occ.txt`; callers that relied on its removal
  must manage their own file lifecycle.
- Reader selection belongs to each calculator. `switch_io_backend_version()`
  changes the default of new bare templates, not existing calculators.
- SCF matches the current STRU, including atom mapping and periodic-equivalent
  positions, and rejects malformed frames. Retained relax/MD behavior selects
  the final frame. This may expose previously silently accepted invalid data.
- Missing Fermi levels remain missing; available values are retained as
  `efermi`. Point-KPT decimal parsing and Cartesian matching units are corrected.

Source attribution and the two upstreams' optimization dispositions are in
[UPSTREAM.md](../UPSTREAM.md) and the [integration audit](upstream-integration.md).

## Validation scope

Built-wheel tests cover Python 3.10/ASE 3.28 and Python 3.12/ASE 3.29, plus
installed ATST/Forge consumer contracts. Example startup tests check
configuration without launching ABACUS. They are interface checks; full
simulation and scientific validation are separate. See the
[cross-repository CI guide](compatibility-ci.md) for engine and workflow
validation.
