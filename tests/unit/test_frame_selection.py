"""Exercise the calculator's SCF result contract and native final-frame collection."""
import re
import shutil
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from ase import Atoms
from ase.units import Bohr

from abacuslite.core import AbacusTemplate
from abacuslite.io.legacyio import read_abacus_out


TESTFILES = Path(__file__).resolve().parents[1] / "fixtures"
GOLD = TESTFILES / "multiframe_scf_trial_last"
LTS_ROUNDED_CELL = TESTFILES / "lts_scf_cell_rounding"

STRU_FRAME_FORCES = np.array([[-0.5, -0.01, 0.0], [0.5, 0.01, 0.0], [0.0, 0.0, 0.0]])
LAST_FRAME_FORCES = np.array([[-0.45, -0.014, 0.0], [0.45, 0.014, 0.0], [0.0, 0.0, 0.0]])
MD_LEGACY_FORCES = np.array(
    [[1.0712942948, 2.1781413019, 1.2152201133],
     [-1.0712942948, -2.1781413019, -1.2152201133]]
)
MD_LATEST_FORCES = np.array(
    [[0.1191299488, 0.2678988387, 1.5033416041],
     [-0.1191299488, -0.2678988387, -1.5033416041]]
)
MD_LEGACY_ENERGY = -1940.5509086572
MD_LATEST_ENERGY = -1940.6311063727


def _template(calc="scf", atomorder=None, legacy=True):
    template = AbacusTemplate()
    template.suffix = "ABACUS"
    template.calculation = calc
    template.atomorder = atomorder
    template._legacyio = legacy
    return template


def _write_fixture(directory, source, calculation="scf", log_text=None):
    (directory / "STRU").write_text((GOLD / "STRU").read_text())
    output = directory / "OUT.ABACUS"
    output.mkdir()
    log = output / f"running_{calculation}.log"
    log.write_text(source.read_text() if log_text is None else log_text)
    return log


def _md_fixture_legacy(directory):
    shutil.copytree(TESTFILES / "multiframe_md_legacy", directory / "OUT.ABACUS")
    return directory


def _md_fixture_latest(directory):
    shutil.copytree(TESTFILES / "multiframe_md_latest", directory / "OUT.ABACUS")
    return directory


def test_scf_read_results_rejects_multiple_geometry_records(tmp_path):
    """The raw reader can inspect the synthetic trajectory; SCF requires one record."""
    log = _write_fixture(tmp_path, GOLD / "running_scf.log")
    assert len(read_abacus_out(log)) == 4
    with pytest.raises(RuntimeError) as excinfo:
        _template().read_results(tmp_path)
    assert str(log) in str(excinfo.value)


def test_native_relax_multiframe_returns_last_result(tmp_path):
    _write_fixture(tmp_path, GOLD / "running_scf.log", calculation="relax")
    results = _template(calc="relax").read_results(tmp_path)
    np.testing.assert_allclose(results["forces"], LAST_FRAME_FORCES, atol=1e-12)


def _rounded_cell_run(tmp_path):
    """Copy the attributed one-frame LTS output without modifying its geometry."""
    shutil.copytree(LTS_ROUNDED_CELL, tmp_path, dirs_exist_ok=True)
    return _template(atomorder=[0]), tmp_path


def test_lts_rounded_log_cell_matches_without_abacus_json(tmp_path):
    """Six-significant-digit lattice rounding is accepted."""
    template, directory = _rounded_cell_run(tmp_path)
    assert not (directory / "abacus.json").exists()

    results = template.read_results(directory)
    assert results["energy"] == pytest.approx(-13.5410411603)
    np.testing.assert_allclose(results["forces"], [[0, 0, 0]], atol=1e-12)


@pytest.mark.parametrize("logged_vector,matches", [("101.234", True), ("101.235", False)])
def test_lts_large_cell_compares_at_logged_precision(tmp_path, logged_vector, matches):
    template, directory = _rounded_cell_run(tmp_path)
    stru = directory / "STRU"
    stru.write_text(stru.read_text().replace("10.000016522100001", "101.23445"))
    log = directory / "OUT.ABACUS" / "running_scf.log"
    log.write_text(log.read_text().replace("+10 ", f"+{logged_vector} ", 1))
    if matches:
        assert template.read_results(directory)["energy"] == pytest.approx(-13.5410411603)
    else:
        with pytest.raises(RuntimeError):
            template.read_results(directory)


@pytest.mark.parametrize("scale", [1.234564321, 1.2345652])
def test_lts_rounded_cell_nonunit_alat_and_nonorthogonal_vectors(tmp_path, scale):
    """The default identity tolerance accepts rounding in the printed lattice data."""
    template, directory = _rounded_cell_run(tmp_path)
    # LTS prints the rounded Angstrom line with its own 0.529177 constant;
    # at the second value this differs from rounding with ASE's Bohr value.
    lts_printed_scale = (scale / Bohr) * 0.529177
    vectors = np.array([[10.0000165221, 0.25, 0],
                        [0, 11.000002299, 0.5],
                        [0.125, 0, 11.9999880759]])
    stru = directory / "STRU"
    text = stru.read_text().replace(
        "1.8897261258369282", str(scale / Bohr)
    ).replace(
        "10.000016522100001 0.0 0.0\n"
        "0.0 11.000002299 0.0\n"
        "0.0 0.0 11.999988075900001",
        "\n".join(" ".join(map(str, row)) for row in vectors),
    )
    stru.write_text(text)

    log_path = directory / "OUT.ABACUS" / "running_scf.log"
    lines = log_path.read_text().splitlines()
    header = next(i for i, line in enumerate(lines)
                  if line.strip() ==
                  "Lattice vectors: (Cartesian coordinate: in unit of a_0)")
    lines[header + 1:header + 4] = [
        " ".join(f"{value:+.6g}" for value in row) for row in vectors
    ]
    lines = [line.replace("lattice constant (Angstrom) = 1",
                          f"lattice constant (Angstrom) = {lts_printed_scale:.6g}")
             .replace("1.889726125837 Bohr ).", f"{scale / Bohr:.12f} Bohr ).")
             for line in lines]
    log_path.write_text("\n".join(lines) + "\n")

    assert abs(10 * float(f"{lts_printed_scale:.6g}") - vectors[0, 0] * scale) > 1e-5
    results = template.read_results(directory)
    assert results["energy"] == pytest.approx(-13.5410411603)


def test_native_md_legacy_keeps_last_frame_semantics_real_gold(tmp_path):
    """Native legacy MD returns its final logged frame without requiring a STRU."""
    directory = _md_fixture_legacy(tmp_path)
    results = _template(calc="md", atomorder=[0, 1]).read_results(directory)
    assert np.allclose(results["forces"], MD_LEGACY_FORCES, atol=1e-12)
    assert results["energy"] == pytest.approx(MD_LEGACY_ENERGY)
    assert results["free_energy"] == pytest.approx(MD_LEGACY_ENERGY)
    assert results["energy_without_entropy"] == pytest.approx(-1940.3851061129, abs=1e-9)


def test_native_md_latestio_md_dump_keeps_last_frame_semantics(tmp_path):
    """Native latest-format MD returns the final MD_dump frame without a STRU."""
    directory = _md_fixture_latest(tmp_path)
    results = _template(calc="md", atomorder=[0, 1], legacy=False).read_results(directory)
    assert np.allclose(results["forces"], MD_LATEST_FORCES, atol=1e-12)
    assert results["energy"] == pytest.approx(MD_LATEST_ENERGY)
    assert results["free_energy"] == pytest.approx(MD_LATEST_ENERGY)
    assert results["energy_without_entropy"] == pytest.approx(-1940.4234898941, abs=1e-9)


def test_scf_validates_geometry_before_reordering(tmp_path, single_point_scf_output):
    log = _write_fixture(tmp_path, single_point_scf_output / "running_scf.log")
    template = _template(atomorder=[0, 2, 1])
    np.testing.assert_allclose(
        template.read_results(tmp_path)["forces"], STRU_FRAME_FORCES[[0, 2, 1]], atol=1e-12
    )
    template.atomorder = [0, 2, 2]
    with pytest.raises(RuntimeError):
        template.read_results(tmp_path)
    template.atomorder = [0, 2, 1]
    text = log.read_text()
    extra = next(line for line in text.splitlines() if line.startswith("taud_Au1"))
    corrupt = text.replace(extra, extra + "\n" + extra.replace("Au1", "Au2"), 1)
    log.write_text(corrupt.replace("TOTAL ATOM NUMBER = 3", "TOTAL ATOM NUMBER = 4"))
    with pytest.raises(RuntimeError):
        template.read_results(tmp_path)


@pytest.mark.parametrize("mode", [
    "Direct", "Cartesian", "Cartesian_au", "Cartesian_angstrom",
    "Cartesian_angstrom_center_xy", "Cartesian_angstrom_center_xz",
    "Cartesian_angstrom_center_yz", "Cartesian_angstrom_center_xyz",
])
def test_scf_coordinate_modes_match_periodic_geometry(tmp_path, single_point_scf_output, mode):
    log = _write_fixture(tmp_path, single_point_scf_output / "running_scf.log")
    cell = np.array([[4., 0., 0.], [1., 5., 0.], [2., 3., 6.]])
    fractions = np.array([[.4, .5, .5], [.6, .5, .5], [.5, .5, .1]])
    shifts = np.array([[1, -2, 0], [-1, 0, 3], [0, 1, -1]])
    positions = fractions @ cell
    lattice_constant = 2.
    coordinates = {
        "Direct": fractions,
        "Cartesian": positions / (lattice_constant * Bohr),
        "Cartesian_au": positions / Bohr,
        "Cartesian_angstrom": positions,
    }
    if mode.startswith("Cartesian_angstrom_center_"):
        axes = mode.rsplit("_", 1)[-1]
        offset = cell.sum(axis=0) / 2.0 * [axis in axes for axis in "xyz"]
        coordinates[mode] = positions - offset
    text = log.read_text()
    for i, label in enumerate(("taud_H1", "taud_H2", "taud_Au1")):
        wrapped = fractions[i] + shifts[i]
        raw_line = next(line for line in text.splitlines() if line.startswith(label))
        raw_fields = raw_line.split()
        text = text.replace(raw_line,
                            " ".join([label, *map(str, wrapped), *raw_fields[4:]]))
    lattice_vectors = cell / (lattice_constant * Bohr)
    logged_scale = lattice_constant * 0.529177
    text = re.sub(r"(lattice constant \(Angstrom\)\s*=\s*)\S+",
                  lambda match: match[1] + f"{logged_scale:.6g}", text, count=1)
    log_vectors = "\n".join(" ".join(f"{value:+.6g}" for value in row)
                            for row in lattice_vectors)
    text = re.sub(r"(Lattice vectors:[^\n]*\n)(?:[^\n]+\n){3}",
                  lambda match: match[1] + log_vectors + "\n", text, count=1)
    log.write_text(text)
    stru_vectors = "\n".join(" ".join(map(str, row)) for row in lattice_vectors)
    coord_lines = [" ".join(map(str, coordinate)) + " mag 0 0 1 sc 1 1 1"
                   for coordinate in coordinates[mode]]
    stru = tmp_path / "STRU"
    stru.write_text(
        "ATOMIC_SPECIES\nH 1 H.upf\nAu 197 Au.upf\n"
        f"LATTICE_CONSTANT\n{lattice_constant}\nLATTICE_VECTORS\n{stru_vectors}\n"
        f"ATOMIC_POSITIONS\n{mode}\nH\n0\n2\n{coord_lines[0]}\n{coord_lines[1]}\n"
        f"Au\n0\n1\n{coord_lines[2]}\n"
    )
    template = _template()
    assert template.read_results(tmp_path)["energy"] == pytest.approx(-2898.)


def test_scf_uses_configured_stru_filename(tmp_path, single_point_scf_output):
    atoms = Atoms("HAuH", positions=[[4, 5, 5], [5, 5, 1], [6, 5, 5]],
                  cell=[10, 10, 10], pbc=True)
    template = _template()
    template.write_input(
        SimpleNamespace(pseudo_dir=None, orbital_dir=None),
        tmp_path, atoms,
        parameters={"calculation": "scf", "stru_file": "CURRENT.STRU"},
        properties=["energy", "forces"],
    )
    shutil.copytree(single_point_scf_output, tmp_path / "OUT.ABACUS")
    (tmp_path / "STRU").write_text("must use the configured STRU path")
    np.testing.assert_allclose(template.read_results(tmp_path)["forces"],
                               STRU_FRAME_FORCES[[0, 2, 1]], atol=1e-12)


def test_write_input_leaves_existing_abacus_json_untouched(tmp_path):
    path = tmp_path / "abacus.json"
    path.write_text('{"old": true}')
    atoms = Atoms("H", positions=[[1, 2, 3]], cell=[10, 11, 12], pbc=True)
    AbacusTemplate().write_input(
        SimpleNamespace(pseudo_dir=None, orbital_dir=None), tmp_path, atoms,
        parameters={"calculation": "scf"}, properties=["energy"],
    )
    assert path.read_text() == '{"old": true}'
    assert not (tmp_path / "abacus.json.bak.0").exists()


def test_scf_read_results_rejects_negative_logged_lattice_constant(tmp_path):
    """A malformed negative alat must not become an otherwise invertible cell."""
    template, directory = _rounded_cell_run(tmp_path)
    assert template.read_results(directory)["energy"] == pytest.approx(-13.5410411603)
    log = directory / 'OUT.ABACUS' / 'running_scf.log'
    text = log.read_text()
    text, count = re.subn(r'(?i)(lattice constant \(Angstrom\)\s*=\s*)([0-9.]+)',
                          r'\g<1>-\2', text)
    assert count == 1
    # Reverse both dimensionless vectors and tau so physical geometry still
    # matches; rejection must come from invalid scale rather than a mismatch.
    lines = text.splitlines()
    header = next(i for i, line in enumerate(lines)
                  if line.strip() == 'Lattice vectors: (Cartesian coordinate: in unit of a_0)')
    for index in range(header + 1, header + 4):
        lines[index] = ' '.join(str(-float(value)) for value in lines[index].split())
    for index, line in enumerate(lines):
        if line.startswith('tauc_'):
            row = line.split()
            row[1:4] = [str(-float(value)) for value in row[1:4]]
            lines[index] = ' '.join(row)
    log.write_text('\n'.join(lines) + '\n')
    with pytest.raises(RuntimeError):
        template.read_results(directory)
