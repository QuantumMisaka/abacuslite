# Tests extracted without semantic changes from the attributed upstream snapshot.
import re
import os
import tempfile
import unittest
from pathlib import Path
from io import TextIOWrapper
from typing import Optional, Dict, List, Any
import numpy as np
from ase.atoms import Atoms
from ase.build import bulk
from ase.constraints import FixAtoms, FixCartesian
from ase.data import chemical_symbols, atomic_masses

from abacuslite.io.generalio import (load_pseudo, load_orbital, file_safe_backup, _write_stru, species_group_indices, _constraint_mobility, write_stru, write_input, _write_kline, _write_ksampl_mp, _write_kpoint, read_kpoint_from_running_log, write_kpt, _parse_coord_line, _atomic_positions_gen, read_stru, read_input, _read_kline, _read_ksampl_mp, _read_kpoint, read_kpt, ATOM_MASS)

class TestAbacusCalculatorIOUtil(unittest.TestCase):

    def setUp(self):
        here = Path(__file__).resolve().parents[1] / 'fixtures/io'
        self.testfiles = here / 'testfiles'

    def test_input_io(self):
        fn = self.testfiles / 'input-script'
        data = read_input(fn)
        with tempfile.NamedTemporaryFile(mode='w') as f:
            fn_ = Path(f.name)
            write_input(data, fn_.as_posix())
            data_ = read_input(fn_.as_posix())
            self.assertDictEqual(data, data_)
        # will automatically delete the file after the context manager

    def test_file_safe_backup_rotates_numbered_backups(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            live = workdir / 'STRU'
            live.write_text('live')
            (workdir / 'STRU.bak.0').write_text('bak0')
            (workdir / 'STRU.bak.1').write_text('bak1')
            (workdir / 'STRU.bak.01').write_text('bak01')
            (workdir / 'STRU.bak.note').write_text('note')

            file_safe_backup(live)

            self.assertFalse(live.exists())
            self.assertEqual((workdir / 'STRU.bak.0').read_text(), 'live')
            self.assertEqual((workdir / 'STRU.bak.1').read_text(), 'bak0')
            self.assertEqual((workdir / 'STRU.bak.2').read_text(), 'bak1')
            self.assertEqual((workdir / 'STRU.bak.01').read_text(), 'bak01')
            self.assertEqual((workdir / 'STRU.bak.note').read_text(), 'note')

    def test_stru_io(self):
        from ase.units import Bohr, Angstrom
        nacl = bulk('NaCl', 'rocksalt', a=5.64)
        write_stru(
            nacl,
            outdir=self.testfiles,
            pp_file={
                'Na': 'Na.pz-bhs.UPF',
                'Cl': 'Cl.pz-bhs.UPF'
            },
            orb_file={
                'Na': 'Na_gga_6au_100Ry_2s2p1d.orb',
                'Cl': 'Cl_gga_6au_100Ry_2s2p1d.orb',
            },
        )
        stru_ = read_stru(self.testfiles / 'STRU')
        (self.testfiles / 'STRU').unlink()

        self.assertIsInstance(stru_, dict)
        for k in ['lat', 'species', 'coord_type']:
            self.assertIn(k, stru_)
        for k in ['const', 'vec']:
            self.assertIn(k, stru_['lat'])
        for k in ['symbol', 'mass', 'pp_file', 'orb_file', 'mag_each', 'natom', 'atom']:
            for s in stru_['species']:
                self.assertIn(k, s)
        self.assertEqual(stru_['coord_type'], 'Cartesian')

        self.assertEqual(stru_['lat']['const'], Angstrom / Bohr)
        self.assertTrue(np.allclose(stru_['lat']['vec'], np.array(nacl.get_cell())))
        self.assertIsInstance(stru_['species'], list)

        for s in stru_['species']:
            self.assertIsInstance(s, dict)
            self.assertEqual(s['natom'], 1)
            self.assertIsInstance(s['atom'], list)
            self.assertEqual(s['natom'], len(s['atom']))
            for a in s['atom']:
                self.assertIsInstance(a, dict)
                for k in ['coord', 'm', 'v']:
                    self.assertIn(k, a)
                self.assertEqual(a['m'], [1, 1, 1])
                self.assertEqual(a['v'], [0.0, 0.0, 0.0])

        self.assertEqual(stru_['species'][0]['symbol'], 'Na')
        self.assertEqual(stru_['species'][1]['symbol'], 'Cl')
        self.assertEqual(stru_['species'][0]['mass'], ATOM_MASS['Na'])
        self.assertEqual(stru_['species'][1]['mass'], ATOM_MASS['Cl'])
        self.assertEqual(stru_['species'][0]['pp_file'], 'Na.pz-bhs.UPF')
        self.assertEqual(stru_['species'][1]['pp_file'], 'Cl.pz-bhs.UPF')
        self.assertEqual(stru_['species'][0]['orb_file'], 'Na_gga_6au_100Ry_2s2p1d.orb')
        self.assertEqual(stru_['species'][1]['orb_file'], 'Cl_gga_6au_100Ry_2s2p1d.orb')

    def test_stru_velocities_keep_physical_units_and_species_order(self):
        from ase.units import fs

        atoms = Atoms('HOH', positions=[[0, 0, 0], [1, 0, 0], [2, 0, 0]],
                      cell=[8, 8, 8], pbc=True)
        # One ASE velocity unit is Angstrom per ASE time unit. These inputs
        # represent 1, 2 and -0.5 Angstrom/fs before species grouping.
        atoms.set_velocities(np.array([[1, 0, 0], [0, 2, 0], [0, 0, -0.5]]) / fs)
        # ABACUS md_func.cpp writes MD_dump velocity (Angstrom/fs) as STRU
        # atomic velocity divided by ANGSTROM_AU * AU_to_FS.
        au_per_angstrom_fs = 1.8897270 * 2.418884326505e-2
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_stru(atoms, tmpdir, {'H': 'H.upf', 'O': 'O.upf'})
            species = read_stru(path)['species']
        self.assertEqual([entry['symbol'] for entry in species], ['H', 'O'])
        self.assertEqual([entry['natom'] for entry in species], [2, 1])
        np.testing.assert_allclose([entry['v'] for entry in species[0]['atom']],
                                   np.array([[1, 0, 0], [0, 0, -0.5]]) * au_per_angstrom_fs,
                                   rtol=0, atol=1e-7)
        np.testing.assert_allclose(species[1]['atom'][0]['v'],
                                   [0, 2 * au_per_angstrom_fs, 0], rtol=0, atol=1e-7)

    def test_write_stru_preserves_explicit_mass_for_each_species(self):
        atoms = Atoms('HOH', positions=np.zeros((3, 3)), cell=[8, 8, 8])
        atoms.set_masses([2.014, 15.999, 2.014])
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_stru(atoms, tmpdir, {'H': 'H.upf', 'O': 'O.upf'})
            species = read_stru(path)['species']
        self.assertEqual([entry['symbol'] for entry in species], ['H', 'O'])
        self.assertEqual([entry['mass'] for entry in species], [2.014, 15.999])

    def test_write_stru_rejects_different_masses_within_species_before_writing(self):
        atoms = Atoms('HH', positions=np.zeros((2, 3)), cell=[8, 8, 8])
        atoms.set_masses([1.008, 2.014])
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(ValueError, 'species H'):
                write_stru(atoms, tmpdir, {'H': 'H.upf'})
            self.assertFalse((Path(tmpdir) / 'STRU').exists())

    def test_read_stru_with_lattice_parameter(self):
        # STRU that uses LATTICE_PARAMETER instead of LATTICE_VECTORS
        # (issue #7555: previously raised KeyError on 'LATTICE_PARAMETERS')
        content = (
            "ATOMIC_SPECIES\n"
            "Si 28.085 Si.upf\n"
            "\n"
            "LATTICE_CONSTANT\n"
            "10.2\n"
            "\n"
            "LATTICE_PARAMETER\n"
            "5.43 5.43 5.43 90 90 90\n"
            "\n"
            "ATOMIC_POSITIONS\n"
            "Direct\n"
            "\n"
            "Si\n"
            "0.0\n"
            "2\n"
            "0.0 0.0 0.0 1 1 1\n"
            "0.25 0.25 0.25 1 1 1\n"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            fn = Path(tmpdir) / 'STRU'
            fn.write_text(content)
            stru = read_stru(fn)
        self.assertEqual(stru['lat']['const'], 10.2)
        self.assertNotIn('vec', stru['lat'])
        self.assertEqual(stru['lat']['param'], [5.43, 5.43, 5.43, 90.0, 90.0, 90.0])
        self.assertEqual(stru['species'][0]['symbol'], 'Si')
        self.assertEqual(stru['species'][0]['natom'], 2)

    def test_write_stru_preserves_first_occurrence_species_order(self):
        atoms = Atoms(
            symbols=['C', 'C', 'Pt', 'H', 'H'],
            positions=np.zeros((5, 3)),
            cell=np.eye(3),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            write_stru(
                atoms,
                outdir=tmpdir,
                pp_file={'C': 'C.upf', 'Pt': 'Pt.upf', 'H': 'H.upf'},
            )
            stru = read_stru(Path(tmpdir) / 'STRU')

        self.assertEqual([s['symbol'] for s in stru['species']], ['C', 'Pt', 'H'])
        self.assertEqual([s['natom'] for s in stru['species']], [2, 1, 2])

    def test_write_stru_uses_ase_constraints_for_mobility(self):
        atoms = Atoms(
            symbols=['C', 'C', 'Pt', 'H'],
            positions=np.zeros((4, 3)),
            cell=np.eye(3),
        )
        atoms.set_constraint([
            FixAtoms(indices=[0]),
            FixCartesian(2, mask=[True, False, True]),
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            write_stru(
                atoms,
                outdir=tmpdir,
                pp_file={'C': 'C.upf', 'Pt': 'Pt.upf', 'H': 'H.upf'},
            )
            stru = read_stru(Path(tmpdir) / 'STRU')

        self.assertEqual(stru['species'][0]['atom'][0]['m'], [0, 0, 0])
        self.assertEqual(stru['species'][0]['atom'][1]['m'], [1, 1, 1])
        self.assertEqual(stru['species'][1]['atom'][0]['m'], [0, 1, 0])
        self.assertEqual(stru['species'][2]['atom'][0]['m'], [1, 1, 1])

    def test_kpt_io(self):
        kpt = {
            'mode': 'point',
            'coordinate': 'Cartesian',
            'nk': 1,
            'kpoints': [(0.0, 0.0, 0.0)],
            'weights': [1]
        }
        with tempfile.NamedTemporaryFile(mode='w') as f:
            fn_ = Path(f.name)
            write_kpt(kpt, fn_.as_posix())
            self.assertDictEqual(kpt, read_kpt(fn_.as_posix()))

        kpt = {
            'mode': 'mp-sampling',
            'nk': (5, 5, 5),
            'kshift': (0, 0, 0),
            'gamma-centered': True,
        }
        with tempfile.NamedTemporaryFile(mode='w') as f:
            fn_ = Path(f.name)
            write_kpt(kpt, fn_.as_posix())
            self.assertDictEqual(kpt, read_kpt(fn_.as_posix()))

        # kpt = {
        #     'mode': 'line',
        #     'nk': 6,
        #     'kpoints': [
        #         (0.0, 0.0, 0.0),
        #         (0.5, 0.5, 0.5),
        #         (0.0, 0.5, 0.5),
        #         (0.5, 0.5, 0.0),
        #         (0.5, 0.0, 0.5),
        #         (0.0, 0.0, 0.5),
        #     ],
        #     'nkinterpl': [10, 10, 10, 10, 10, 1],
        #     'coordinate': 'Cartesian',
        # }
        # with tempfile.NamedTemporaryFile(mode='w') as f:
        #     fn_ = Path(f.name)
        #     write_kpt(kpt, fn_.as_posix())
        #     self.assertDictEqual(kpt, read_kpt(fn_.as_posix()))

    def test_load_pseudo(self):
        expected = {
            'O': 'O.upf', 'Si': 'Si.upf', 'In': 'In.upf',
            'As': 'As.pbe-n-rrkjus_psl.0.2.UPF',
            'Ga': 'Ga.pbe-dn-kjpaw_psl.1.0.0.UPF',
        }
        # These helpers inspect filenames, not pseudopotential contents.
        with tempfile.TemporaryDirectory() as tmpdir:
            for name in [*expected.values(), 'README.md', 'Si.orb']:
                (Path(tmpdir) / name).touch()
            self.assertDictEqual(load_pseudo(tmpdir), expected)

    def test_load_orbital(self):
        common = {'O': 'O_gga_6au_100Ry_2s2p1d.orb',
                  'Si': 'Si_gga_7au_100Ry_2s2p1d.orb'}
        small = 'In_gga_8au_100Ry_1s1p1d.orb'
        large = 'In_gga_8au_100Ry_2s2p2d1f.orb'
        with tempfile.TemporaryDirectory() as tmpdir:
            for name in [*common.values(), large, small, 'README.md', 'In.upf']:
                (Path(tmpdir) / name).touch()
            self.assertDictEqual(load_orbital(tmpdir), {**common, 'In': small})
            self.assertDictEqual(load_orbital(tmpdir, efficiency=False), {**common, 'In': large})

    def test_write_stru_with_magmom(self):
        # from issue #6516: https://github.com/deepmodeling/abacus-develop/issues/6516
        atoms = Atoms(
            symbols=['Co', 'Cr', 'Ni', 'Co'],
            cell=np.eye(3),
            magmoms=[1, 2, 3, 1]
        )
        with tempfile.NamedTemporaryFile(mode='w') as f:
            write_stru(
                stru=atoms,
                outdir=self.testfiles,
                pp_file={ # as if we have some pseudopotentials
                    'Co': 'Co.upf', 'Cr': 'Cr.upf', 'Ni': 'Ni.upf', 'Co': 'Co.upf',
                },
                orb_file={ # as if we have some orbitals
                    'Co': 'Co.orb', 'Cr': 'Cr.orb', 'Ni': 'Ni.orb', 'Co': 'Co.orb',
                },
                fname=f.name,
            )
            stru = read_stru(f.name)
        # Co
        self.assertEqual(stru['species'][0]['mag_each'], 0.0)
        self.assertEqual(stru['species'][0]['atom'][0]['mag'], 1.0)
        self.assertEqual(stru['species'][0]['atom'][1]['mag'], 1.0)
        # Cr
        self.assertEqual(stru['species'][1]['mag_each'], 0.0)
        self.assertEqual(stru['species'][1]['atom'][0]['mag'], 2.0)
        # Ni
        self.assertEqual(stru['species'][2]['mag_each'], 0.0)
        self.assertEqual(stru['species'][2]['atom'][0]['mag'], 3.0)

        # then the non-colinear case
        atoms = Atoms(
            symbols=['Co', 'Cr', 'Ni', 'Co'],
            cell=np.eye(3),
            magmoms=np.array([
                [1, 0, 0],
                [0, 2, 0],
                [0, 0, 3],
                [1, 0, 0],
            ])
        )
        with tempfile.NamedTemporaryFile(mode='w') as f:
            write_stru(
                stru=atoms,
                outdir=self.testfiles,
                pp_file={ # as if we have some pseudopotentials
                    'Co': 'Co.upf', 'Cr': 'Cr.upf', 'Ni': 'Ni.upf', 'Co': 'Co.upf',
                },
                orb_file={ # as if we have some orbitals
                    'Co': 'Co.orb', 'Cr': 'Cr.orb', 'Ni': 'Ni.orb', 'Co': 'Co.orb',
                },
                fname=f.name,
            )
            stru = read_stru(f.name)
        # Co
        self.assertEqual(stru['species'][0]['mag_each'], 0.0)
        self.assertEqual(stru['species'][0]['atom'][0]['mag'], ('Cartesian', [1.0, 0.0, 0.0]))
        self.assertEqual(stru['species'][0]['atom'][1]['mag'], ('Cartesian', [1.0, 0.0, 0.0]))
        # Cr
        self.assertEqual(stru['species'][1]['mag_each'], 0.0)
        self.assertEqual(stru['species'][1]['atom'][0]['mag'], ('Cartesian', [0.0, 2.0, 0.0]))
        # Ni
        self.assertEqual(stru['species'][2]['mag_each'], 0.0)
        self.assertEqual(stru['species'][2]['atom'][0]['mag'], ('Cartesian', [0.0, 0.0, 3.0]))
