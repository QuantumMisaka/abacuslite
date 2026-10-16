"""Check example environment handoff before any ABACUS process is launched."""

import os
from pathlib import Path
import subprocess
import sys

import pytest


EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


@pytest.mark.parametrize("name", [
    "scf", "relax", "cellrelax", "bandstructure", "dos", "md",
    "constraintmd", "metadynamics", "neb", "soc", "socketio",
])
def test_example_profile_uses_explicit_environment(name, tmp_path):
    assets = tmp_path / "assets with spaces"
    assets.mkdir()
    # A subprocess contains the SOC example's ASE global-property changes.
    # Replace only the constructor call boundary after validating the real
    # profile object. All startup imports and configuration are executed.
    probe = r'''
import os
from pathlib import Path
import runpy
import sys
import abacuslite

class ProfileChecked(Exception):
    pass

original = abacuslite.AbacusProfile

def check_profile(*args, **kwargs):
    profile = original(*args, **kwargs)
    assert str(profile.pseudo_dir) == os.environ['ABACUS_PP_ORB']
    assert str(profile.orbital_dir) == os.environ['ABACUS_PP_ORB']
    assert profile.command == os.environ['ABACUS_COMMAND']
    raise ProfileChecked

abacuslite.AbacusProfile = check_profile
try:
    runpy.run_path(sys.argv[1], run_name='__main__')
except ProfileChecked:
    pass
else:
    raise AssertionError('Example did not construct an ABACUS profile')
'''
    env = {**os.environ, "ABACUS_PP_ORB": str(assets),
           "ABACUS_COMMAND": "custom-mpirun -np 2 custom-abacus", "MPLBACKEND": "Agg"}
    result = subprocess.run([sys.executable, "-c", probe, str(EXAMPLES / f"{name}.py")],
                            cwd=tmp_path, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
