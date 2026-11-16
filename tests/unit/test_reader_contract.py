"""Public output-reader geometry, stream and atom-order contracts."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
import shutil

import numpy as np
import pytest

from abacuslite.io import latestio, legacyio


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _mock_reader_data():
    frame = {
        "elem": ["Na", "Na", "Cl"],
        "coords": np.array(
            [
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0],
                [2.0, 0.0, 0.0],
            ]
        ),
        "cell": np.eye(3),
        "coordinate": "Cartesian",
        "alat_in_angstrom": 1.0,
    }
    elecstate = [
        {
            "k": np.zeros((1, 1, 3)),
            "e": np.zeros((1, 1, 1)),
            "occ": np.ones((1, 1, 1)),
        }
    ]
    energies = [{"E_KohnSham": -1.0, "E_Fermi": 0.0}]
    kpoints = ((np.zeros((1, 3)), np.ones(1), None), None, None, None, None)
    magmoms = [np.array([10.0, 20.0, 30.0])]
    forces = [np.array([[1.0, 0.0, 0.0], [2.0, 0.0, 0.0], [3.0, 0.0, 0.0]])]
    return frame, elecstate, energies, kpoints, magmoms, forces


def _patch_reader(module, monkeypatch, frame, elecstate, energies, kpoints, magmoms, forces):
    monkeypatch.setattr(module, "read_esolver_type_from_running_log", lambda lines: "ksdft")
    monkeypatch.setattr(module, "read_traj_from_running_log", lambda lines: [frame])
    monkeypatch.setattr(module, "read_forces_from_running_log", lambda lines: forces)
    monkeypatch.setattr(module, "read_stress_from_running_log", lambda lines: [])
    monkeypatch.setattr(module, "read_kpoints_from_running_log", lambda lines: kpoints)
    monkeypatch.setattr(module, "read_energies_from_running_log", lambda lines: ([], energies))
    monkeypatch.setattr(module, "read_iter_header_from_running_log", lambda lines: [])
    monkeypatch.setattr(module, "find_final_info_with_iter_header", lambda rows, headers: energies)
    monkeypatch.setattr(module, "read_magmom_from_running_log", lambda lines: magmoms)
    if module is latestio:
        monkeypatch.setattr(module, "read_band_from_eig_occ", lambda path: elecstate)
    else:
        monkeypatch.setattr(module, "read_band_from_running_log", lambda lines: elecstate)


@pytest.mark.parametrize("module", [latestio, legacyio])
@pytest.mark.parametrize("missing_fermi", [False, True])
def test_read_abacus_out_reorders_calculator_magmoms_with_atoms(module, missing_fermi, tmp_path, monkeypatch):
    """Reader result magmoms should follow reordered Atoms indices."""
    running_log = tmp_path / "running_scf.log"
    running_log.write_text("", encoding="utf-8")
    (tmp_path / "eig_occ.txt").write_text("", encoding="utf-8")
    frame, elecstate, energies, kpoints, magmoms, forces = _mock_reader_data()
    if missing_fermi:
        energies[0].pop("E_Fermi")
    _patch_reader(module, monkeypatch, frame, elecstate, energies, kpoints, magmoms, forces)

    atoms = module.read_abacus_out(running_log, sort_atoms_with=[0, 2, 1])[0]

    assert atoms.get_chemical_symbols() == ["Na", "Cl", "Na"]
    np.testing.assert_allclose(atoms.cell.array, np.eye(3))
    assert np.all(atoms.pbc)
    np.testing.assert_allclose(atoms.get_initial_magnetic_moments(), [10.0, 30.0, 20.0])
    np.testing.assert_allclose(atoms.calc.results["magmoms"], [10.0, 30.0, 20.0])
    # Forces must follow the same atom ordering as the returned Atoms object.
    np.testing.assert_allclose(
        atoms.calc.results["forces"],
        [[1.0, 0.0, 0.0], [3.0, 0.0, 0.0], [2.0, 0.0, 0.0]],
    )

    assert atoms.calc.get_fermi_level() == (None if missing_fermi else 0.0)


@pytest.mark.parametrize('source_kind', ['string', 'stream'])
def test_latest_reader_accepts_named_log_sources_without_closing_them(source_kind):
    log = FIXTURES / 'multiframe_md_latest' / 'running_md.log'
    if source_kind == 'string':
        frames = latestio.read_abacus_out(str(log))
    else:
        with log.open() as stream:
            frames = latestio.read_abacus_out(stream)
            assert not stream.closed
    assert len(frames) == 2
    assert frames[-1].get_potential_energy() == pytest.approx(-1940.6311063727)



def test_latest_reader_requires_named_text_stream():
    with pytest.raises(ValueError, match='filesystem name'):
        latestio.read_abacus_out(StringIO(''))



def _geometry_log(source, coordinate, cell, scaled_positions, alat):
    """Derive geometry cases from a recorded SCF without inventing result tables."""
    lines = source.read_text().splitlines()
    cell_header = next(i for i, line in enumerate(lines)
                       if line.strip() == 'Lattice vectors: (Cartesian coordinate: in unit of a_0)')
    lines[cell_header + 1:cell_header + 4] = [
        ' '.join(f'{component / alat:.12f}' for component in vector) for vector in cell
    ]
    header = next(i for i, line in enumerate(lines)
                  if line.lstrip().startswith('CARTESIAN COORDINATES'))
    lines[header] = coordinate.upper() + ' COORDINATES'
    values = scaled_positions if coordinate == 'Direct' else scaled_positions @ cell / alat
    for atom_index, position in enumerate(values):
        row = lines[header + 2 + atom_index].split()
        row[0] = row[0].replace('tauc_', 'taud_') if coordinate == 'Direct' else row[0]
        row[1:4] = [f'{component:.12f}' for component in position]
        lines[header + 2 + atom_index] = ' '.join(row)
    for index, line in enumerate(lines):
        if 'lattice constant (angstrom)' in line.lower():
            lines[index] = line.split('=')[0] + f'= {alat}'
    return '\n'.join(lines) + '\n'



@pytest.mark.parametrize('reader,name', [(latestio, 'latest'), (legacyio, 'legacy')])
@pytest.mark.parametrize('coordinate', ['Direct', 'Cartesian'])
@pytest.mark.parametrize('geometry', ['triclinic', 'vacuum'])
def test_output_atoms_have_cartesian_angstrom_geometry(
    reader, name, coordinate, geometry, tmp_path
):
    """Public ASE geometry is physical even for Direct logs and vacuum supercells."""
    source = FIXTURES / 'noncollinear_scf' / name
    if geometry == 'triclinic':
        cell = np.array([[4., 0., 0.], [1., 6., 0.], [.5, 1., 8.]])
        fractions = np.array([[.1, .2, .3], [.6, .7, .8]])
        expected = [[.75, 1.5, 2.4], [3.5, 5., 6.4]]
    else:
        # A compact pair surrounded by vacuum still uses ABACUS's simulation box.
        cell = np.diag([20., 24., 28.])
        fractions = np.array([[.5, .5, .5], [.62, .5, .5]])
        expected = [[10., 12., 14.], [12.4, 12., 14.]]
    log = tmp_path / 'running_scf.log'
    log.write_text(_geometry_log(source / log.name, coordinate, cell, fractions, alat=2.))
    if name == 'latest':
        shutil.copy2(source / 'eig_occ.txt', tmp_path / 'eig_occ.txt')
    raw = reader.read_traj_from_running_log(log)[0]
    atoms = reader.read_abacus_out(log, index=0, sort_atoms_with=[1, 0])

    np.testing.assert_allclose(atoms.get_positions(), expected[::-1], atol=1e-11, rtol=0)
    np.testing.assert_allclose(atoms.cell.array, cell, atol=1e-11, rtol=0)
    assert atoms.pbc.all()
    np.testing.assert_allclose(raw['coords'], fractions if coordinate == 'Direct'
                               else fractions @ cell / 2., atol=1e-11, rtol=0)
    assert raw['coordinate'] == coordinate
    if geometry == 'vacuum':
        assert atoms.get_distance(0, 1) == pytest.approx(2.4)
