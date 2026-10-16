"""Real installed consumer boundaries; no engine execution or vendored fallback.

These checks intentionally fail on missing consumers when --run-consumers is
selected. Expectations come from retained output fixtures, not a second call
through the candidate parser.
"""

import importlib.metadata
from pathlib import Path
import shlex
import shutil
import sys

import numpy as np
import pytest


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture(autouse=True)
def installed_packages():
    import abacuslite
    import atst_tools
    import abacus_forge
    from atst_tools.calculators.abacuslite_backend import Abacus, BACKEND_SOURCE
    from abacuslite import Abacus as CandidateAbacus

    for module, distribution in [(abacuslite, "abacuslite"), (atst_tools, "atst-tools"),
                                  (abacus_forge, "abacus-forge")]:
        assert Path(module.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
        print(distribution, importlib.metadata.version(distribution), module.__file__)
    assert BACKEND_SOURCE == "external"
    assert Abacus is CandidateAbacus


def test_atst_input_preparation_uses_installed_writers(tmp_path):
    from ase import Atoms
    from ase.io import write
    from atst_tools.utils.abacus_io import prepare_abacus_input_from_config
    from abacuslite.io.generalio import read_input, read_stru, read_kpt

    structure = tmp_path / "atoms.extxyz"
    write(structure, Atoms("HPtH", positions=[[1, 2, 3], [4, 5, 6], [2, 3, 4]],
                           cell=[10, 10, 10], pbc=True))
    config = {"calculator": {"name": "abacus", "abacus": {
        "kpts": [2, 3, 4], "parameters": {
            "calculation": "scf", "ecutwfc": 80,
            "pseudopotentials": {"H": "H.upf", "Pt": "Pt.upf"},
            "basissets": {"H": "H.orb", "Pt": "Pt.orb"},
        }}}}
    output = tmp_path / "inputs"
    prepare_abacus_input_from_config(config, str(structure), str(output))
    assert read_input(output / "INPUT")["ecutwfc"] == "80"
    assert read_kpt(output / "KPT")["nk"] == (2, 3, 4)
    parsed = read_stru(output / "STRU")
    assert [species["symbol"] for species in parsed["species"]] == ["H", "Pt"]
    np.testing.assert_allclose(parsed["species"][0]["atom"][1]["coord"], [2, 3, 4])


def test_atst_profile_and_ase_calculator_preserve_scf_forces_and_fermi(tmp_path, monkeypatch):
    from ase import Atoms
    from atst_tools.calculators.abacuslite_backend import Abacus, ATSTAbacusProfile

    # Only the engine subprocess is replaced; real ATST profile, ASE dispatch,
    # input writer, atom reordering and output readers remain exercised.
    profile = ATSTAbacusProfile("unused-abacus", version_command=shlex.join([
        sys.executable, "-c", "print('ABACUS v3.10.1')"
    ]))
    def engine_output(directory, *args, **kwargs):
        output = Path(directory) / "OUT.ABACUS"
        output.mkdir(exist_ok=True)
        shutil.copy(FIXTURES / "multiframe_scf_trial_last/running_scf.log", output)
    monkeypatch.setattr(profile, "run", engine_output)
    calc = Abacus(profile, directory=tmp_path,
                  pseudopotentials={"H": "H.upf", "Au": "Au.upf"},
                  basissets={"H": "H.orb", "Au": "Au.orb"})
    atoms = Atoms("HAuH", positions=[[4, 5, 5], [5, 5, 1], [6, 5, 5]],
                  cell=[10, 10, 10], pbc=True, calculator=calc)
    np.testing.assert_allclose(atoms.get_forces(), [[-.5, -.01, 0], [0, 0, 0], [.5, .01, 0]])
    assert atoms.get_potential_energy() == pytest.approx(-2898.0, rel=0, abs=1e-8)
    assert calc.results["efermi"] == pytest.approx(-2.04)


@pytest.mark.parametrize("backend,version,energy,forces", [
    ("legacy", "v3.10.1", -1940.4680073850,
     [[1.0712942948, 2.1781413019, 1.2152201133], [-1.0712942948, -2.1781413019, -1.2152201133]]),
    ("latest", "v3.11.0", -1940.5272981334,
     [[.1191299488, .2678988387, 1.5033416041], [-.1191299488, -.2678988387, -1.5033416041]]),
])
def test_forge_collects_installed_parser_facts_read_only(tmp_path, backend, version, energy, forces):
    from abacus_forge.collection import collect_contained
    from abacus_forge.workspace import Workspace

    workspace = Workspace(tmp_path).ensure_layout()
    log = (FIXTURES / f"multiframe_md_{backend}/running_md.log").read_text()
    workspace.write_text("outputs/running_md.log", f"ABACUS VERSION: {version}\n" + log)
    workspace.write_text("inputs/INPUT", "INPUT_PARAMETERS\ncalculation md\nsuffix ABACUS\n")
    # Forge projects E_KS(sigma->0) when present; ASE calculator energy uses E_KohnSham.
    before = (workspace.outputs_dir / "running_md.log").read_bytes()
    for _ in range(2):
        result = collect_contained(workspace, parser_backend="abacuslite", output_version=version)
        assert result.diagnostics["parser"]["actual_backend"] == "abacuslite"
        assert result.diagnostics["parser"]["io_backend"] == backend + "io"
        assert result.metrics["total_energy"] == pytest.approx(energy, rel=0, abs=1e-8)
        np.testing.assert_allclose(np.asarray(result.metrics["force"]).reshape(-1, 3), forces)
    assert (workspace.outputs_dir / "running_md.log").read_bytes() == before
