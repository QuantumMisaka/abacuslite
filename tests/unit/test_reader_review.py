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
