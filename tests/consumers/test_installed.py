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
    from atst_tools.calculators.abacuslite_backend import (
        Abacus, BACKEND_SOURCE, import_generalio, import_latestio,
        import_legacyio, import_ksampling,
    )
    from abacuslite import Abacus as CandidateAbacus

    for module, distribution in [(abacuslite, "abacuslite"), (atst_tools, "atst-tools"),
                                  (abacus_forge, "abacus-forge")]:
        assert Path(module.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
        print(distribution, importlib.metadata.version(distribution), module.__file__)
    assert BACKEND_SOURCE == "external"
    assert Abacus is CandidateAbacus
    assert import_generalio().__name__ == "abacuslite.io.generalio"
    assert import_latestio().__name__ == "abacuslite.io.latestio"
    assert import_legacyio().__name__ == "abacuslite.io.legacyio"
    assert import_ksampling().__name__ == "abacuslite.utils.ksampling"
    assert not any(name.startswith("atst_tools.external.ASE_interface.abacuslite")
                   for name in sys.modules)
    yield
    assert not any(name.startswith("atst_tools.external.ASE_interface.abacuslite")
                   for name in sys.modules)


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
    assert calc.results["fermi_level"] == pytest.approx(-2.04)


def test_atst_periodic_scf_handoff_fails_closed_on_unmatched_structure(tmp_path, monkeypatch):
    from ase import Atoms
    from atst_tools.calculators.abacuslite_backend import Abacus, ATSTAbacusProfile

    profile = ATSTAbacusProfile("unused-abacus", version_command=shlex.join([
        sys.executable, "-c", "print('ABACUS v3.10.1')"
    ]))

    def engine_output(directory, *args, **kwargs):
        output = Path(directory) / "OUT.ABACUS"
        output.mkdir(exist_ok=True)
        shutil.copy(FIXTURES / "multiframe_scf_trial_last/running_scf.log", output)

    monkeypatch.setattr(profile, "run", engine_output)
    wrapped = Abacus(profile, directory=tmp_path / "wrapped",
                     pseudopotentials={"H": "H.upf", "Au": "Au.upf"},
                     basissets={"H": "H.orb", "Au": "Au.orb"})
    atoms = Atoms("HAuH", positions=[[14, 5, 5], [5, 5, 1], [-4, 5, 5]],
                  cell=[10, 10, 10], pbc=True, calculator=wrapped)
    np.testing.assert_allclose(atoms.get_forces(),
                               [[-.5, -.01, 0], [0, 0, 0], [.5, .01, 0]])

    unmatched = Abacus(profile, directory=tmp_path / "unmatched",
                       pseudopotentials={"H": "H.upf", "Au": "Au.upf"},
                       basissets={"H": "H.orb", "Au": "Au.orb"})
    atoms = Atoms("HAuH", positions=[[4.123, 5, 5], [5, 5, 1], [6, 5, 5]],
                  cell=[10, 10, 10], pbc=True, calculator=unmatched)
    with pytest.raises(RuntimeError, match="fail-closed"):
        atoms.get_forces()


def test_atst_native_md_frames_keep_physical_cell_and_raw_cartesian_positions(tmp_path):
    from atst_tools.workflows.md import AbacusNativeMDRunner

    source = FIXTURES / "multiframe_md_latest"
    output = tmp_path / "OUT.ABACUS"
    output.mkdir()
    (tmp_path / "INPUT").write_text("INPUT_PARAMETERS\nsuffix ABACUS\n")
    originals = {name: (source / name).read_bytes()
                 for name in ("running_md.log", "MD_dump", "eig_occ.txt")}
    for name in originals:
        (output / name).write_bytes(originals[name])

    runner = AbacusNativeMDRunner({}, "abacus", {"directory": str(tmp_path)})
    frames = runner._collect_frames()
    assert len(frames) == 2
    for frame in frames:
        assert frame.pbc.all()
        np.testing.assert_allclose(frame.cell.array[0],
                                   [2.82684765869, 2.82684765869, 0],
                                   rtol=0, atol=1e-9)
        assert frame.get_volume() == pytest.approx(45.1791, rel=0, abs=1e-4)
    np.testing.assert_allclose(frames[-1].positions[1],
                               [0.025620321279, 2.822443204757, 2.834296002714],
                               rtol=0, atol=1e-12)
    np.testing.assert_allclose(frames[-1].get_forces(),
                               [[.1191299488, .2678988387, 1.5033416041],
                                [-.1191299488, -.2678988387, -1.5033416041]],
                               rtol=0, atol=1e-8)
    assert frames[-1].get_potential_energy() == pytest.approx(-1940.6311063727,
                                                               rel=0, abs=1e-8)
    assert {name: (output / name).read_bytes() for name in originals} == originals


@pytest.mark.parametrize("order", [("legacy", "latest"), ("latest", "legacy")])
def test_atst_selected_calculators_keep_mixed_output_readers_isolated(tmp_path, order):
    from atst_tools.calculators.abacuslite_backend import Abacus, ATSTAbacusProfile
    from abacuslite import core

    versions = {"legacy": "v3.10.1", "latest": "v3.11.0"}
    energies = {"legacy": -1940.5509086572, "latest": -1940.6311063727}
    calculators = {}
    previous_default = core.__LEGACYIO__
    try:
        for name in order:
            directory = tmp_path / name
            profile = ATSTAbacusProfile("unused-abacus", version_command=shlex.join([
                sys.executable, "-c", f"print('ABACUS {versions[name]}')"
            ]))
            calculators[name] = Abacus(profile, directory=directory)
            shutil.copytree(FIXTURES / f"multiframe_md_{name}", directory / "OUT.ABACUS")
            calculators[name].template.suffix = "ABACUS"
            calculators[name].template.calculation = "md"
        for compatibility_default in ("v3.11.0", "v3.10.1"):
            core.switch_io_backend_version(compatibility_default)
            for name in reversed(order):
                result = calculators[name].template.read_results(tmp_path / name)
                assert result["energy"] == pytest.approx(energies[name], rel=0, abs=1e-8)
    finally:
        core.__LEGACYIO__ = previous_default


def test_atst_selected_latest_reader_preserves_eig_occ_on_repeated_reads(tmp_path):
    from atst_tools.calculators.abacuslite_backend import import_latestio

    source = FIXTURES / "multiframe_md_latest"
    originals = {name: (source / name).read_bytes()
                 for name in ("running_md.log", "MD_dump", "eig_occ.txt")}
    for name, content in originals.items():
        (tmp_path / name).write_bytes(content)
    reader = import_latestio().read_abacus_out
    first = reader(tmp_path / "running_md.log")
    second = reader(tmp_path / "running_md.log")
    assert len(first) == len(second) == 2
    for one, two in zip(first, second):
        assert one.get_potential_energy() == pytest.approx(two.get_potential_energy(), abs=0)
        np.testing.assert_array_equal(one.get_forces(), two.get_forces())
        np.testing.assert_array_equal(one.calc.kpts[0].eps_n, two.calc.kpts[0].eps_n)
        np.testing.assert_array_equal(one.calc.kpts[0].f_n, two.calc.kpts[0].f_n)
    assert first[-1].get_potential_energy() == pytest.approx(-1940.6311063727, abs=1e-8)
    np.testing.assert_allclose(first[-1].get_forces()[0],
                               [.1191299488, .2678988387, 1.5033416041], atol=1e-8)
    assert first[0].calc.kpts[0].eps_n[0] == pytest.approx(-8.734940678442698)
    assert first[-1].calc.kpts[0].eps_n[0] == pytest.approx(-8.466362211457593)
    assert {name: (tmp_path / name).read_bytes() for name in originals} == originals


def test_atst_input_paths_and_cp_guard_use_external_writers(tmp_path):
    from ase import Atoms
    from ase.io import write
    from atst_tools.utils.abacus_io import prepare_abacus_input_from_config
    from abacuslite.io.generalio import read_input

    base = tmp_path / "config-base"
    base.mkdir()
    structure = base / "atoms.extxyz"
    write(structure, Atoms("H", positions=[[1, 2, 3]], cell=[8, 8, 8], pbc=True))
    config = {"calculator": {"name": "abacus", "abacus": {
        "parameters": {"calculation": "scf", "pseudo_dir": "pp",
                       "orbital_dir": "orb", "basis_type": "pw"},
        "pseudopotentials": {"H": "H.upf"},
    }}}
    output = tmp_path / "inputs"
    prepare_abacus_input_from_config(config, str(structure), str(output),
                                     config_base_dir=base)
    parsed = read_input(output / "INPUT")
    assert parsed["pseudo_dir"] == str((base / "pp").resolve())
    assert parsed["orbital_dir"] == str((base / "orb").resolve())

    config["calculator"]["constant_potential"] = {"target_potential": 0.0}
    config["calculator"]["abacus"]["parameters"]["nupdown"] = 0
    rejected = tmp_path / "cp-rejected"
    with pytest.raises(ValueError, match="nupdown"):
        prepare_abacus_input_from_config(config, str(structure), str(rejected),
                                         config_base_dir=base)
    assert not rejected.exists()


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
