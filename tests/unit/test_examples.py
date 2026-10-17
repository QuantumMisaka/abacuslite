"""Check example environment handoff before any ABACUS process is launched."""

import os
from pathlib import Path
import subprocess
import shutil
import sys

import pytest


EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


@pytest.mark.parametrize("name", [
    "scf", "relax", "cellrelax", "bandstructure", "dos", "md",
    "constraintmd", "metadynamics", "neb", "soc", "socketio",
])
@pytest.mark.parametrize("override_command", [False, True])
def test_example_configuration_uses_own_directory_and_engine_settings(name, override_command, tmp_path):
    assets = tmp_path / "assets with spaces"
    assets.mkdir()
    # A subprocess contains the SOC example's ASE global-property changes.
    # Replace the calculator constructor before version detection or execution.
    # Use a copied script so example cleanup cannot touch checkout artifacts.
    example = tmp_path / f"{name}.py"
    shutil.copyfile(EXAMPLES / example.name, example)
    probe = r'''
import os
from pathlib import Path
import runpy
import shlex
import sys
import abacuslite

class ConfigurationChecked(Exception):
    pass

original = abacuslite.AbacusProfile

def check_profile(*args, **kwargs):
    profile = original(*args, **kwargs)
    assert str(profile.pseudo_dir) == os.environ['ABACUS_PP_ORB']
    assert str(profile.orbital_dir) == os.environ['ABACUS_PP_ORB']
    if 'ABACUS_COMMAND' in os.environ:
        assert profile.command == os.environ['ABACUS_COMMAND']
    else:
        assert shlex.split(profile.command)[-1] == 'abacus'
    return profile

def check_calculator(*args, **kwargs):
    directory = Path(kwargs['directory']).resolve()
    assert directory.parent == Path(sys.argv[1]).parent
    assert directory.name.startswith(Path(sys.argv[1]).stem), directory
    raise ConfigurationChecked

abacuslite.AbacusProfile = check_profile
abacuslite.Abacus = check_calculator
abacuslite.AbacusSocketIO = check_calculator
try:
    runpy.run_path(sys.argv[1], run_name='__main__')
except ConfigurationChecked:
    pass
else:
    raise AssertionError('Example did not configure an ABACUS calculator')
'''
    env = {**os.environ, "ABACUS_PP_ORB": str(assets), "MPLBACKEND": "Agg"}
    env.pop("ABACUS_COMMAND", None)
    if override_command:
        env["ABACUS_COMMAND"] = "custom-mpirun -np 2 custom-abacus"
    if sys.flags.isolated:
        shadow = tmp_path / "source-shadow" / "abacuslite"
        shadow.mkdir(parents=True)
        (shadow / "__init__.py").write_text("raise RuntimeError('PYTHONPATH shadow imported')\n")
        env["PYTHONPATH"] = str(shadow.parent)
    command = [sys.executable, *(["-I"] if sys.flags.isolated else []), "-c", probe, str(example)]
    result = subprocess.run(command,
                            cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
