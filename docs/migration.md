# Installing and migrating to independent abacuslite

The independent package retains the ABACUS plugin's ASE calculator design and
module responsibilities. The `src` layout separates installable code from
examples and test assets; consumers still import `abacuslite`.

## Architecture comparison

A source-level audit at independent baseline `97d6850` found all 66 publicly
named function/method definitions (including constructors) from ABACUS
`4b92455ca` present with the same argument signatures. All 60 corresponding
ATST definitions at `45d8c78` are also present with the same signatures.
The additional public methods relative to ATST come from newer ABACUS socket
support and `Abacus.write_input`. Test classes and private helpers were excluded
from those counts. They are audit observations, not a source-hash CI contract
or proof that every behavior is identical.

The ASE inheritance remains `AbacusProfile(BaseProfile)`,
`AbacusTemplate(CalculatorTemplate)`, `Abacus(GenericFileIOCalculator)` and
`AbacusSocketIO(SocketIOCalculator)`. General input I/O, output readers and
K-point helpers remain in their original modules. ATST's launcher/workflow
policy remains in ATST. There is no new scheduler, service layer or runtime
consumer dependency.

The current runtime is deliberately close to upstream, including a relatively
large `core.py`. Internal modularization can be considered when maintenance
requires it; moving classes now would create migration work without being
necessary for independent packaging.

## Install one implementation

Use a fresh virtual environment for initial validation, following README.md.
Install the [published stable package](https://pypi.org/project/abacuslite/1.1.0/)
with `pip install 'abacuslite==1.1.0'`. See the
[release record](superpowers/plans/2026-10-17-1.1.0-release.md) for artifact
identities and fresh indexed-install verification.
For development use `pip install .` and record the exact source revision.
The earlier `1.1.0rc1` label covered several source iterations and does not
uniquely identify those pre-release builds.

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
| Direct `atst_tools.external.ASE_interface.abacuslite...` import | Maintainer migration is required: use ATST's adapter for calculators/profile policy, or `abacuslite.io...` for pure I/O |
| Forge collection | Keep the explicit optional parser selection and native default; validate the supported plugin/Forge pair |
| Running tests from the old production modules | Use `pytest` against `tests/`; fixtures and examples ship in sdist, not the runtime wheel |
| Examples relying on ABACUS's parent-directory layout | Set `ABACUS_PP_ORB` and `ABACUS_COMMAND`; install the package before running |

During transition, do not remove the ATST fallback until direct vendored callers
and supported deployment environments have migrated. A compatibility module,
if needed, should forward to the independent implementation. It should not keep
a second parser implementation or move ATST launcher policy into this package.

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

## What has been validated

Built-wheel and sdist-derived-wheel tests cover Python 3.10/ASE 3.28 and
Python 3.12/ASE 3.29, plus bounded installed ATST/Forge consumer contracts.
Startup tests for all 11 examples verify their configured asset path and engine
command without launching ABACUS. They do not execute full simulations.

Real engine acceptance and production dependency migration remain separate
steps. Before publishing or deploying a consumer pair, run the intended engine
and affected workflows with independent reference results; see the
[cross-repository CI guide](compatibility-ci.md). Architecture continuity and
installation success alone do not establish scientific compatibility.
