"""Installed-package contracts exercised without accessing plugin internals.

Only the external engine launch/version probe is replaced. Input writing,
format selection, parsing and the ASE calculator handoff remain real.
"""

from pathlib import Path
import re
import shutil

import numpy as np
import pytest
from ase import Atoms

from abacuslite import Abacus, AbacusProfile
from abacuslite.io import latestio, legacyio
from abacuslite.io.generalio import read_input, read_kpt, read_stru
from abacuslite.io.generalio import write_input, write_kpt, write_stru


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


class ReplayProfile(AbacusProfile):
    """A controlled launcher which returns recorded engine output."""

    def __init__(self, version, output):
        super().__init__("unused-engine")
        self.engine_version = version
        self.output = output

    def version(self):
        return self.engine_version

    def run(self, directory, inputfile, outputfile, errorfile=None, append=False):
        assert inputfile is None
        assert read_input(Path(directory) / "INPUT")
        destination = Path(directory) / "OUT.ABACUS"
        destination.mkdir(exist_ok=True)
        for path in self.output.iterdir():
            if (path.name in {"running_scf.log", "running_md.log", "eig_occ.txt", "MD_dump"}
                    or re.fullmatch(r"eig_occg\d+\.txt", path.name)):
                shutil.copy2(path, destination / path.name)


@pytest.mark.parametrize("order", [("legacy", "latest"), ("latest", "legacy")])
def test_independent_calculators_select_formats_through_public_calls(tmp_path, order):
    versions = {"legacy": "v3.10.1", "latest": "v3.11.0-beta10"}
    expected = {"legacy": -1940.5509086572, "latest": -1940.6311063727}
    atoms = {}
    for name in order:
        atoms[name] = Atoms("AsGa", positions=[[1.4, 1.4, 1.4], [0, 0, 0]],
                            cell=[6, 6, 6], pbc=True)
        atoms[name].calc = Abacus(
            profile=ReplayProfile(versions[name], FIXTURES / f"multiframe_md_{name}"),
            directory=tmp_path / name,
            pseudopotentials={"As": "As.upf", "Ga": "Ga.upf"},
            inp={"calculation": "md", "basis_type": "pw", "gamma_only": True},
        )
    for name in reversed(order):
        assert atoms[name].get_potential_energy() == pytest.approx(expected[name])
        assert atoms[name].get_potential_energy(force_consistent=True) == pytest.approx(expected[name])
        assert atoms[name].get_forces().shape == (2, 3)
    assert atoms["legacy"].calc.results["energy_without_entropy"] == pytest.approx(-1940.3851061129)


@pytest.mark.parametrize("layout,available", [
    ("overwrite", [False, True]),
    ("append", [True, True]),
    ("numbered", [True, True]),
    ("missing_final", [True, False]),
    ("missing_all", [False, False]),
])
def test_develop_md_spectra_follow_ionic_steps(tmp_path, layout, available):
    source = FIXTURES / "multiframe_md_latest"
    output = tmp_path / "recorded"
    output.mkdir()
    shutil.copy2(source / "MD_dump", output)
    log = output / "running_md.log"
    # Keep the recorded trajectory but replace its producer announcements
    # with those for the layout under test.
    text = re.sub(r"(?im)^ *Write eigenvalues and occupations to file:.*\n",
                  "", (source / log.name).read_text())
    spectrum = (source / "eig_occ.txt").read_text()
    split_at = spectrum.index("2     # ionic step")
    first, last = spectrum[:split_at], spectrum[split_at:]
    last = last.replace("2     # ionic step", "# Ionic_Step 2", 1)
    last, count = re.subn(r"(?m)^(\s*1\s+\S+\s+)\S+", r"\g<1>-2.5E-1", last, count=1)
    assert count == 1
    if layout in {"overwrite", "append"}:
        (output / "eig_occ.txt").write_text(last if layout == "overwrite" else first + last)
        text += "\n Write Eigenvalues and occupations to file: OUT.ABACUS/eig_occ.txt\n"
    else:
        # The stale fixed file must not be used, even if announced files are gone.
        (output / "eig_occ.txt").write_text("stale spectrum\n")
        for step, frame, is_available in zip((1, 2), (first, last), available):
            name = f"eig_occg{step}.txt"
            text += f"\n Write Eigenvalues and occupations to file: OUT.ABACUS/{name}\n"
            if is_available:
                (output / name).write_text(frame)
    log.write_text(text)

    with log.open() as stream:
        frames = latestio.read_abacus_out(stream)
        assert not stream.closed
    assert [frame.calc.get_eigenvalues() is not None for frame in frames] == available
    assert [frame.get_potential_energy() for frame in frames] == pytest.approx(
        [-1940.6273962477, -1940.6311063727])

    atoms = Atoms("AsGa", cell=[6, 6, 6], pbc=True)
    atoms.calc = Abacus(
        profile=ReplayProfile("v3.11.0-beta10", output), directory=tmp_path / "run",
        pseudopotentials={"As": "As.upf", "Ga": "Ga.upf"},
        inp={"calculation": "md", "basis_type": "pw", "gamma_only": True},
    )
    assert atoms.get_potential_energy() == pytest.approx(-1940.6311063727)
    assert atoms.calc.results["fermi_level"] == pytest.approx(9.0922469042)
    assert atoms.get_forces().shape == (2, 3)
    exported = atoms.calc.export_properties()
    assert ("eigenvalues" in exported) is available[-1]
    assert ("occupations" in exported) is available[-1]
    if available[-1]:
        assert exported["occupations"][0, 0, 0] == pytest.approx(-0.25)


def test_scf_restores_interleaved_atom_order(tmp_path, single_point_scf_output):
    atoms = Atoms("HAuH", positions=[[4, 5, 5], [5, 5, 1], [6, 5, 5]],
                  cell=[10, 10, 10], pbc=True)
    atoms.calc = Abacus(
        profile=ReplayProfile("v3.10.1", single_point_scf_output),
        directory=tmp_path,
        pseudopotentials={"H": "H.upf", "Au": "Au.upf"},
        inp={"basis_type": "pw", "gamma_only": True, "cal_force": True},
    )
    np.testing.assert_allclose(atoms.get_forces(),
                               [[-0.5, -0.01, 0], [0, 0, 0], [0.5, 0.01, 0]])
    assert atoms.calc.results["efermi"] == pytest.approx(-2.04)
    assert atoms.calc.results["fermi_level"] == pytest.approx(-2.04)
    assert "energy_without_entropy" not in atoms.calc.results


def test_scf_collects_final_parsed_result(tmp_path):
    source = FIXTURES / "multiframe_scf_trial_last"
    log = source / "running_scf.log"
    count = len(legacyio.read_abacus_out(log))
    assert count == 4
    atoms = Atoms("HHAu", positions=[[4, 5, 5], [6, 5, 5], [5, 5, 1]],
                  cell=[10, 10, 10], pbc=True)
    atoms.calc = Abacus(
        profile=ReplayProfile("v3.10.1", source),
        directory=tmp_path, pseudopotentials={"H": "H.upf", "Au": "Au.upf"},
        inp={"basis_type": "pw", "gamma_only": True},
    )
    np.testing.assert_allclose(atoms.get_forces(),
                               [[-0.45, -0.014, 0], [0.45, 0.014, 0], [0, 0, 0]])


def test_scf_collects_results_without_rereading_stru(tmp_path, single_point_scf_output):
    class OutputOnlyProfile(ReplayProfile):
        def run(self, directory, inputfile, outputfile, errorfile=None, append=False):
            super().run(directory, inputfile, outputfile, errorfile, append)
            stru = Path(directory) / "STRU"
            stru.rename(stru.with_suffix(".used"))

    atoms = Atoms("HHAu", positions=[[4, 5, 5], [6, 5, 5], [5, 5, 1]],
                  cell=[10, 10, 10], pbc=True)
    atoms.calc = Abacus(
        profile=OutputOnlyProfile("v3.10.1", single_point_scf_output),
        directory=tmp_path, pseudopotentials={"H": "H.upf", "Au": "Au.upf"},
        inp={"basis_type": "pw", "gamma_only": True},
    )
    assert atoms.get_potential_energy() == pytest.approx(-2898.0)


def test_calculator_preserves_existing_abacus_json(tmp_path):
    marker = tmp_path / "abacus.json"
    marker.write_text('{"old": true}')
    atoms = Atoms("H", positions=[[1, 2, 3]], cell=[10, 11, 12], pbc=True)
    calc = Abacus(
        profile=ReplayProfile("v3.10.1", tmp_path), directory=tmp_path,
        pseudopotentials={"H": "H.upf"},
        inp={"basis_type": "pw", "gamma_only": True},
    )
    calc.write_input(atoms, properties=["energy"])
    assert marker.read_text() == '{"old": true}'
    assert list(tmp_path.glob("abacus.json*")) == [marker]


@pytest.mark.parametrize("name,reader,energy", [
    ("latest", latestio.read_abacus_out, -1940.6311063727),
    ("legacy", legacyio.read_abacus_out, -1940.5509086572),
])
def test_output_readers_are_repeatable_indexed_and_read_only(tmp_path, name, reader, energy):
    output = tmp_path / name
    shutil.copytree(FIXTURES / f"multiframe_md_{name}", output)
    before = {path.name: path.read_bytes() for path in output.iterdir()}
    log = output / "running_md.log"
    frames = reader(log)
    selected = reader(log, index=-1)
    assert isinstance(frames, list) and len(frames) == (2 if name == "latest" else 1)
    assert isinstance(selected, Atoms)
    assert selected.get_potential_energy() == pytest.approx(energy)
    assert selected.get_potential_energy(force_consistent=True) == pytest.approx(energy)
    np.testing.assert_allclose(selected.get_forces(), frames[-1].get_forces())
    reordered = reader(log, index=-1, sort_atoms_with=[1, 0])
    assert reordered.get_chemical_symbols() == selected.get_chemical_symbols()[::-1]
    np.testing.assert_allclose(reordered.get_forces(), selected.get_forces()[::-1])
    assert {path.name: path.read_bytes() for path in output.iterdir()} == before


@pytest.mark.parametrize("name,version,reader", [
    ("latest", "v3.11.0-beta10", latestio.read_abacus_out),
    ("legacy", "v3.10.1", legacyio.read_abacus_out),
])
def test_noncollinear_results_need_no_global_ase_patch(tmp_path, name, version, reader):
    source = FIXTURES / "noncollinear_scf" / name
    # Compare the public reader's values with the file-backed handoff.
    # Independent raw-table assertions belong to the real-engine harness.
    frame = reader(source / "running_scf.log", index=-1)
    moments = frame.get_magnetic_moments()
    assert moments.shape == (2, 3)
    assert np.all(np.linalg.norm(moments, axis=1) > 1e-3)
    energy = frame.get_potential_energy()
    atoms = Atoms("Fe2", positions=[[0, 0, 0], [2.6, 2.6, 2.6]],
                  cell=[5.2, 5.2, 5.2], pbc=True, magmoms=[[1, 0, 0], [0, 1, 0]])
    atoms.calc = Abacus(
        profile=ReplayProfile(version, source), directory=tmp_path,
        pseudopotentials={"Fe": "Fe.upf"},
        inp={"basis_type": "pw", "gamma_only": True, "nspin": 4},
    )
    assert atoms.get_potential_energy() == pytest.approx(energy)
    np.testing.assert_allclose(atoms.calc.results["magmoms"], moments)
    assert atoms.calc.results["eigenvalues"].shape[-1] > 0
    exported = atoms.calc.export_properties()
    assert exported["energy"] == pytest.approx(energy)
    assert "fermi_level" in exported
    assert atoms.calc.results["efermi"] == exported["fermi_level"]
    assert "efermi" not in exported
    assert "magmoms" not in exported
    assert "energy_without_entropy" not in exported
    assert atoms.get_properties(["energy"])["energy"] == pytest.approx(energy)
    # A noncollinear calculation must not make later collinear ASE result
    # conversion reject its scalar per-atom moments.
    collinear = legacyio.read_abacus_out(
        FIXTURES / "multiframe_scf_trial_last" / "running_scf.log", index=-1)
    assert np.asarray(collinear.calc.properties()["magmoms"]).shape == (3,)


def test_top_level_writer_imports():
    from abacuslite import write_kpt as public_write_kpt
    from abacuslite import write_stru as public_write_stru

    assert public_write_stru is write_stru
    assert public_write_kpt is write_kpt


def test_input_io_without_an_engine_preserves_declared_values(tmp_path):
    write_input({"suffix": "public", "scf_thr": 1e-8}, tmp_path / "INPUT")
    assert read_input(tmp_path / "INPUT") == {"suffix": "public", "scf_thr": "1e-08"}
    sampling = {"mode": "mp-sampling", "gamma-centered": True,
                "nk": (2, 3, 4), "kshift": (0, 0, 0)}
    write_kpt(sampling, tmp_path / "KPT")
    assert read_kpt(tmp_path / "KPT") == sampling
    atoms = Atoms("HHeH", positions=[[0, 0, 0], [1, 1, 1], [2, 2, 2]],
                  cell=[5, 5, 5], pbc=True)
    atoms.set_masses([2.014, 4.003, 2.014])
    write_stru(atoms, tmp_path, {"H": "H.upf", "He": "He.upf"})
    data = read_stru(tmp_path / "STRU")
    assert [item["symbol"] for item in data["species"]] == ["H", "He"]
    assert [item["mass"] for item in data["species"]] == pytest.approx([2.014, 4.003])


@pytest.mark.parametrize("module,header,marker", [
    (latestio, "--> #ION MOVE# 1 #ELEC ITER#", "#"),
    (legacyio, "LCAO ALGORITHM ---- ION=1 ELEC=", ""),
])
@pytest.mark.parametrize("source_kind", ["path", "string", "lines"])
def test_selected_log_fields_keep_units_shapes_and_missing_values(
        tmp_path, module, header, marker, source_kind):
    # Literal independent tables: two electronic iterations, one ionic step.
    content = f"""{header} 1
ENERGY Rydberg eV
E_KohnSham -1.0 -13.6
end
{header} 2
ENERGY Rydberg eV
E_KohnSham -2.0 -27.2
E_Fermi 0.1 1.36
end
{marker}TOTAL-FORCE (eV/Angstrom){marker}
Si1 1.0 -2.0 3.0
Si2 -1.0 2.0 -3.0
end
{marker}TOTAL-STRESS (kbar){marker}
1.0 0.0 0.0
0.0 2.0 0.0
0.0 0.0 -3.0
end
"""
    log = tmp_path / "running_scf.log"
    log.write_text(content)
    src = {"path": log, "string": str(log), "lines": content.splitlines()}[source_kind]
    rydberg, ev = module.read_energies_from_running_log(src)
    assert rydberg[-1] == {"E_KohnSham": -2.0, "E_Fermi": 0.1}
    assert ev == [{"E_KohnSham": -13.6}, {"E_KohnSham": -27.2, "E_Fermi": 1.36}]
    headers = module.read_iter_header_from_running_log(src)
    assert headers == [(1, 1), (1, 2)]
    assert module.find_final_info_with_iter_header(ev, headers) == [ev[-1]]
    np.testing.assert_allclose(module.read_forces_from_running_log(src),
                               [[[1, -2, 3], [-1, 2, -3]]])
    np.testing.assert_allclose(module.read_stress_from_running_log(src),
                               [np.diag([-0.0006241509, -0.0012483018, 0.0018724527])],
                               rtol=1e-6, atol=0)
    assert module.read_energies_from_running_log(["no energy table"]) == ([], [])
    assert module.read_forces_from_running_log(["no force table"]) == []
    assert module.read_stress_from_running_log(["no stress table"]) == []
