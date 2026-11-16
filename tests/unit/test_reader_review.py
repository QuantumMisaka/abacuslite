"""Regressions for coordinate tokens and file-backed reader semantics."""

from io import StringIO
from pathlib import Path

import numpy as np
import pytest

from abacuslite.io import latestio, legacyio
from abacuslite.io.generalio import _parse_coord_line


FIXTURES = Path(__file__).resolve().parents[1] / 'fixtures'


@pytest.mark.parametrize('tail', ['m 1 0', 'v 1 2', 'mag 1 2',
                                 'mag 1 angle1 90', 'mag 1 angle2 0',
                                 'mag 1 angle1 90 angle2'])
def test_coordinate_keywords_reject_incomplete_values(tail):
    with pytest.raises(ValueError):
        _parse_coord_line('0 0 0 ' + tail)


def test_coordinate_keywords_are_grouped_by_name():
    atom = _parse_coord_line(
        '0 0 0 velocity +1e-2 -2E+1 0 magmom +1e0 -1e-1 0 m 1 0 1')
    assert atom == {'coord': [0., 0., 0.], 'v': [.01, -20., 0.],
                    'mag': ('Cartesian', [1., -.1, 0.]), 'm': [1, 0, 1]}
    spherical = _parse_coord_line('0 0 0 angle2 -90 mag 1 m 1 1 1 angle1 45')
    assert spherical['mag'] == ('Spherical', [1., 45., -90.])


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


@pytest.mark.parametrize('reader,name', [(latestio, 'latest'), (legacyio, 'legacy')])
def test_periodicity_is_independent_of_trajectory_source(reader, name):
    atoms = reader.read_abacus_out(
        FIXTURES / 'noncollinear_scf' / name / 'running_scf.log', index=-1)
    assert np.all(atoms.pbc)


@pytest.mark.parametrize('tail', ['unknown 1', 'mag 1 magmom 2', 'm 1 2 0'])
def test_coordinate_keywords_reject_unknown_duplicate_and_invalid_flags(tail):
    with pytest.raises(ValueError, match='Unknown|Duplicate|Mobility'):
        _parse_coord_line('0 0 0 ' + tail)


def test_latest_reader_requires_named_text_stream():
    with pytest.raises(ValueError, match='filesystem name'):
        latestio.read_abacus_out(StringIO(''))


@pytest.mark.parametrize('tail,expected_moment', [
    ('v 1 2 3 1 0 1', None),
    ('mag 1 -2 3 1 0 1', ('Cartesian', [1., -2., 3.])),
    ('mag 1 angle1 45 angle2 90 1 0 1', ('Spherical', [1., 45., 90.])),
])
def test_bare_mobility_follows_complete_atom_property(tail, expected_moment):
    atom = _parse_coord_line('0 0 0 ' + tail)
    assert atom['m'] == [1, 0, 1]
    if expected_moment is not None:
        assert atom['mag'] == expected_moment
    else:
        assert atom['v'] == [1., 2., 3.]


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
    import shutil

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
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
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
        atoms.set_pbc(False)  # Nonperiodic analysis is an explicit caller choice.
        assert not atoms.pbc.any()
        np.testing.assert_allclose(atoms.get_positions(), expected[::-1], atol=1e-11, rtol=0)
    assert before == {path.name: path.read_bytes() for path in tmp_path.iterdir()}
