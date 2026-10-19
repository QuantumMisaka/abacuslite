# Tests extracted without semantic changes from the attributed upstream snapshot.
import re
import shutil
import tempfile
import unittest
from io import TextIOWrapper
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from ase.atoms import Atoms
from ase.calculators.singlepoint import (
    SinglePointKPoint,
    SinglePointDFTCalculator
)
from ase.units import Ry, eV, GPa, bar
from ase.stress import full_3x3_to_voigt_6_stress

from abacuslite.io.legacyio import (parse_kpoints_table, read_kpoints_from_running_log, read_esolver_type_from_running_log, read_band_from_running_log, read_traj_from_running_log, read_traj_from_md_dump, read_forces_from_running_log, read_stress_from_running_log, read_energies_from_running_log, read_magmom_from_running_log, read_iter_header_from_running_log, find_final_info_with_iter_header, is_invalid_arr, read_abacus_out, __all__)

class TestLegacyIO(unittest.TestCase):

    here = Path(__file__).resolve().parents[1] / 'fixtures/io'
    testfiles = here / 'testfiles'

    def test_real_lts_native_md_uses_dump_frames_and_preserves_raw_files(self):
        source = Path(__file__).resolve().parents[1] / 'fixtures/lts_native_md'
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir)
            original = {name: (source / name).read_bytes()
                        for name in ('running_md.log', 'MD_dump')}
            for name, content in original.items():
                (out / name).write_bytes(content)
            frames = read_abacus_out(out / 'running_md.log')
            self.assertEqual(len(frames), 3)
            self.assertEqual(read_iter_header_from_running_log(out / 'running_md.log')[-1],
                             (3, 1))
            expected_energies = [-210.6232157020, -210.6231743578, -210.6230563530]
            for frame, energy in zip(frames, expected_energies):
                self.assertTrue(np.all(frame.pbc))
                self.assertEqual(frame.get_chemical_symbols(), ['Si', 'Si'])
                self.assertAlmostEqual(frame.get_potential_energy(), energy, delta=1e-8)
            self.assertTrue(np.allclose(frames[0].cell.array[0],
                                        [0, 2.714998919, 2.714998919], atol=1e-8))
            self.assertTrue(np.allclose(frames[-1].positions[0],
                                        [2.715919335449, 2.715708402644, 5.429380230519],
                                        rtol=0, atol=1e-10))
            self.assertTrue(np.allclose(frames[-1].get_forces()[0],
                                        [-0.089751265334, -0.069019542505, 0.059917431359],
                                        rtol=0, atol=1e-8))
            self.assertEqual({name: (out / name).read_bytes() for name in original}, original)

    def test_lts_native_md_missing_or_truncated_dump_fails_clearly(self):
        source = Path(__file__).resolve().parents[1] / 'fixtures/lts_native_md'
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir)
            shutil.copyfile(source / 'running_md.log', out / 'running_md.log')
            with self.assertRaisesRegex(ValueError, 'running_md.log.*1.*3'):
                read_abacus_out(out / 'running_md.log')
            dump = (source / 'MD_dump').read_text()
            (out / 'MD_dump').write_text(dump[:dump.index('MDSTEP:  2')])
            with self.assertRaisesRegex(ValueError, 'MD_dump.*frame'):
                read_abacus_out(out / 'running_md.log')
            last_step, tail = dump.split('MDSTEP:  2')
            lines = [line for line in tail.splitlines()
                     if not line.strip().startswith('1  Si')]
            (out / 'MD_dump').write_text(last_step + 'MDSTEP:  2\n' + '\n'.join(lines))
            with self.assertRaisesRegex(ValueError, 'Invalid or truncated MD_dump'):
                read_abacus_out(out / 'running_md.log')

    def test_complete_legacy_md_log_without_dump_retains_physical_geometry(self):
        source = Path(__file__).resolve().parents[1] / 'fixtures/multiframe_md_legacy/running_md.log'
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / 'running_md.log'
            original = source.read_bytes()
            path.write_bytes(original)
            frames = read_abacus_out(path)
            self.assertEqual(len(frames), 1)
            self.assertTrue(np.all(frames[0].pbc))
            self.assertAlmostEqual(frames[0].get_potential_energy(), -1940.5509086572)
            # The raw log has Direct (0.25, 0.25, 0.25), a0=0.529177 A,
            # and a cell with rows (5.34197, 5.34197, 0) cyclically.
            expected_cell = np.array([[5.34197, 5.34197, 0],
                                      [0, 5.34197, 5.34197],
                                      [5.34197, 0, 5.34197]]) * 0.529177
            np.testing.assert_allclose(frames[0].cell.array, expected_cell, rtol=0, atol=1e-12)
            np.testing.assert_allclose(frames[0].positions[0],
                                       np.array([0.25, 0.25, 0.25]) @ expected_cell,
                                       rtol=0, atol=1e-12)
            self.assertEqual(path.read_bytes(), original)

    def test_complete_cartesian_md_log_without_dump_converts_alat(self):
        source = Path(__file__).resolve().parents[1] / 'fixtures/multiframe_md_legacy/running_md.log'
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / 'running_md.log'
            original = source.read_text().replace('DIRECT COORDINATES\n', 'CARTESIAN COORDINATES\n', 1)
            original = original.replace('taud_As1            0.2500000000        0.2500000000        0.2500000000',
                                        'tauc_As1            2.0000000000        0.0000000000        0.0000000000', 1)
            original = original.replace('taud_Ga1', 'tauc_Ga1', 1)
            path.write_text(original)
            frames = read_abacus_out(path)
            self.assertEqual(len(frames), 1)
            np.testing.assert_allclose(frames[0].positions[0], [2 * 0.529177, 0, 0],
                                       rtol=0, atol=1e-12)
            self.assertTrue(np.all(frames[0].pbc))
            self.assertEqual(path.read_text(), original)

    def test_read_band_from_running_log(self):
        # nspin1
        fn = self.testfiles / 'lcao-symm1-nspin1-multik-scf_'
        data = read_band_from_running_log(fn)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertTrue(all('k' in d and 'e' in d and 'occ' in d for d in data))
        nspin, nk, nband = data[0]['e'].shape
        self.assertEqual(nspin, 1)
        self.assertEqual(nband, 24)
        self.assertEqual(nk, 2)
        for d in data: # for each frame
            self.assertTrue(d['k'].shape == (nspin, nk, 3))
            self.assertTrue(d['e'].shape == (nspin, nk, nband))
            self.assertTrue(d['occ'].shape == (nspin, nk, nband))

        # nspin2
        fn = self.testfiles / 'lcao-symm0-nspin2-multik-relax_'
        data = read_band_from_running_log(fn)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertTrue(all('k' in d and 'e' in d and 'occ' in d for d in data))
        nspin, nk, nband = data[0]['e'].shape
        self.assertEqual(nspin, 2)
        self.assertEqual(nband, 24)
        self.assertEqual(nk, 2)
        for d in data: # for each frame
            self.assertTrue(d['k'].shape == (nspin, nk, 3))
            self.assertTrue(d['e'].shape == (nspin, nk, nband))
            self.assertTrue(d['occ'].shape == (nspin, nk, nband))

        # nspin 2, cell-relax (multi-frames)
        fn = self.testfiles / 'lcao-symm0-nspin2-multik-cellrelax_'
        data = read_band_from_running_log(fn)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2) # two frames
        self.assertTrue(all('k' in d and 'e' in d and 'occ' in d for d in data))
        nspin, nk, nband = data[0]['e'].shape
        self.assertEqual(nspin, 2)
        self.assertEqual(nband, 40)
        self.assertEqual(nk, 2)
        for d in data: # for each frame
            self.assertTrue(d['k'].shape == (nspin, nk, 3))
            self.assertTrue(d['e'].shape == (nspin, nk, nband))
            self.assertTrue(d['occ'].shape == (nspin, nk, nband))

        # nspin 2, MD (multi-frames)
        fn = self.testfiles / 'pw-symm0-nspin4-gamma-md_'
        data = read_band_from_running_log(fn)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 3)
        self.assertTrue(all('k' in d and 'e' in d and 'occ' in d for d in data))
        nspin, nk, nband = data[0]['e'].shape
        self.assertEqual(nspin, 1)
        self.assertEqual(nband, 35)
        self.assertEqual(nk, 1)
        for d in data: # for each frame
            self.assertTrue(d['k'].shape == (nspin, nk, 3))
            self.assertTrue(d['e'].shape == (nspin, nk, nband))
            self.assertTrue(d['occ'].shape == (nspin, nk, nband))

    def test_read_band_from_running_log_skips_non_band_rows(self):
        data = read_band_from_running_log([
            'nspin = 1',
            'NBANDS = 2',
            'nkstot = 1',
            '1/1 kpoint (Cartesian) = 0.0 0.0 0.0 (1 pws)',
            'BAND ENERGY OCCUPATION',
            '1 -1.0 1.0',
            '2 0.5 0.0',
        ])

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['e'].shape, (1, 1, 2))
        self.assertTrue(np.allclose(data[0]['e'][0, 0], [-1.0, 0.5]))
        self.assertTrue(np.allclose(data[0]['occ'][0, 0], [1.0, 0.0]))

    def test_read_band_from_running_log_does_not_cross_kpoint_blocks(self):
        with self.assertRaises(AssertionError):
            read_band_from_running_log([
                'nspin = 1',
                'NBANDS = 2',
                'nkstot = 2',
                '1/2 kpoint (Cartesian) = 0.0 0.0 0.0 (1 pws)',
                '1 -1.0 1.0',
                '2/2 kpoint (Cartesian) = 0.5 0.0 0.0 (1 pws)',
                '1 -0.5 1.0',
                '2 0.5 0.0',
            ])

    def test_read_abacus_out_reorders_calculator_magmoms(self):
        import tempfile
        from unittest.mock import patch

        frame = {
            'elem': ['Na', 'Na', 'Cl'],
            'coords': np.array([[0.0, 0.0, 0.0],
                                [1.0, 0.0, 0.0],
                                [2.0, 0.0, 0.0]]),
            'cell': np.eye(3),
        }
        elecstate = [{
            'k': np.zeros((1, 1, 3)),
            'e': np.zeros((1, 1, 1)),
            'occ': np.ones((1, 1, 1)),
        }]
        energies = [{'E_KohnSham': -1.0, 'E_Fermi': 0.0}]
        kpoints = ((np.zeros((1, 3)), np.ones(1), None), None, None, None, None)

        with tempfile.NamedTemporaryFile(mode='w') as f:
            with patch('abacuslite.io.legacyio' + '.read_esolver_type_from_running_log', return_value='ksdft'), \
                 patch('abacuslite.io.legacyio' + '.read_traj_from_running_log', return_value=[frame]), \
                 patch('abacuslite.io.legacyio' + '.read_band_from_running_log', return_value=elecstate), \
                 patch('abacuslite.io.legacyio' + '.read_forces_from_running_log', return_value=[]), \
                 patch('abacuslite.io.legacyio' + '.read_stress_from_running_log', return_value=[]), \
                 patch('abacuslite.io.legacyio' + '.read_kpoints_from_running_log', return_value=kpoints), \
                 patch('abacuslite.io.legacyio' + '.read_energies_from_running_log', return_value=([], [])), \
                 patch('abacuslite.io.legacyio' + '.read_iter_header_from_running_log', return_value=[]), \
                 patch('abacuslite.io.legacyio' + '.find_final_info_with_iter_header', return_value=energies), \
                 patch('abacuslite.io.legacyio' + '.read_magmom_from_running_log', return_value=[np.array([10.0, 20.0, 30.0])]):
                atoms = read_abacus_out(f.name, sort_atoms_with=[0, 2, 1])[0]

        self.assertEqual(atoms.get_chemical_symbols(), ['Na', 'Cl', 'Na'])
        self.assertTrue(np.allclose(atoms.calc.results['magmoms'], [10.0, 30.0, 20.0]))

    def test_read_traj_from_running_log(self):
        fn = self.testfiles / 'lcao-symm1-nspin1-multik-scf_'
        data = read_traj_from_running_log(fn)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1) # it is scf run, only one frame
        self.assertTrue(all('coordinate' in d and 'cell' in d and
                            'elem' in d and 'coords' in d for d in data))
        for d in data:
            self.assertIn(d['coordinate'], ['Cartesian', 'Direct'])
            self.assertEqual(d['cell'].shape, (3, 3))
            self.assertIsInstance(d['elem'], list)
            self.assertEqual(len(d['elem']), 2)

        # relax
        fn = self.testfiles / 'lcao-symm0-nspin2-multik-relax_'
        data = read_traj_from_running_log(fn)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        # relax task will only print the coordinate at the first run
        # but band structure will be printed for multiple times...
        self.assertTrue(all('coordinate' in d and 'cell' in d and
                            'elem' in d and 'coords' in d for d in data))
        for d in data:
            self.assertIn(d['coordinate'], ['Cartesian', 'Direct'])
            self.assertEqual(d['cell'].shape, (3, 3))
            self.assertIsInstance(d['elem'], list)
            self.assertEqual(len(d['elem']), 2)
            self.assertEqual(d['coords'].shape, (2, 3))

        # cell-relax
        fn = self.testfiles / 'lcao-symm0-nspin2-multik-cellrelax_'
        data = read_traj_from_running_log(fn)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 3) # print each time
        self.assertTrue(all('coordinate' in d and 'cell' in d and
                            'elem' in d and 'coords' in d for d in data))
        for d in data:
            self.assertIn(d['coordinate'], ['Cartesian', 'Direct'])
            self.assertEqual(d['cell'].shape, (3, 3))
            self.assertIsInstance(d['elem'], list)
            self.assertEqual(len(d['elem']), 4)
            self.assertEqual(d['coords'].shape, (4, 3))

    def test_read_traj_from_md_dump(self):
        fn = self.testfiles / 'nspin4-gamma-mddump'
        data = read_traj_from_md_dump(fn)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        self.assertTrue(all('coordinate' in d and 'cell' in d and
                            'alat_in_angstrom' in d and 'elem' in d and
                            'coords' in d for d in data))
        for d in data:
            self.assertEqual(d['coordinate'], 'Cartesian')
            self.assertEqual(d['cell'].shape, (3, 3))
            self.assertEqual(d['alat_in_angstrom'], 0.529177000000)
            self.assertIsInstance(d['elem'], list)
            self.assertEqual(len(d['elem']), 2)
            self.assertEqual(d['coords'].shape, (2, 3))

    def test_read_forces_from_running_log(self):
        fn = self.testfiles / 'pw-symm0-nspin4-gamma-md_'
        forces = read_forces_from_running_log(fn)
        self.assertEqual(len(forces), 3) # 3 frames
        self.assertTrue(all(f.shape == (2, 3) for f in forces)) # 2 atoms, 3 components

    def test_read_stress_from_running_log(self):
        fn = self.testfiles / 'lcao-symm0-nspin2-multik-cellrelax_'
        stress = read_stress_from_running_log(fn)
        self.assertEqual(len(stress), 2)
        self.assertTrue(all(s.shape == (3, 3) for s in stress)) # 3x3 matrix

        reference = np.array([
            [ 28.0257165780, -25.0814687477, -25.0814687478],
            [-25.0814687477, -57.2309475134,  52.8147857580],
            [-25.0814687478,  52.8147857580, -57.2309475133],
            [  7.3061116295, -27.6053387696, -27.6053387674],
            [-27.6053387696,   0.8540980637,   7.6367729837],
            [-27.6053387674,   7.6367729837,   0.8540980603],
        ]).reshape(-1, 3, 3)
        for s, sref in zip(stress, reference):
            self.assertTrue(np.allclose(s, -0.1 * GPa * sref))

    def test_read_energies_from_running_log(self):
        fn = self.testfiles / 'lcao-symm0-nspin2-multik-cellrelax_'
        energies_ry, energies_ev = read_energies_from_running_log(fn)
        self.assertIsInstance(energies_ry, list)
        self.assertIsInstance(energies_ev, list)
        self.assertEqual(len(energies_ry), 3)
        self.assertEqual(len(energies_ev), 3)
        self.assertTrue(all(isinstance(e, dict) for e in energies_ry)) # dict of energies
        self.assertTrue(all(isinstance(e, dict) for e in energies_ev))
        for e_ev, e_ry in zip(energies_ev, energies_ry):
            # take energies of one SCF step, there are still many energy terms
            self.assertEqual(len(e_ev), len(e_ry))
            for k, ei_ev in e_ev.items():
                self.assertIn(k, e_ry)
                self.assertAlmostEqual(ei_ev, e_ry[k] * Ry / eV, delta=1e-2)

    def test_read_abacus_out_exposes_entropy_corrected_energy(self):
        """Expose E_KohnSham and the entropy-corrected free energy."""
        source = Path(__file__).resolve().parents[1] / 'fixtures/multiframe_md_legacy/running_md.log'
        atoms = read_abacus_out(source)[-1]

        self.assertAlmostEqual(atoms.get_potential_energy(), -1940.5509086572, delta=1e-9)
        self.assertAlmostEqual(
            atoms.get_potential_energy(force_consistent=True),
            -1940.3851061129,
            delta=1e-9,
        )

    def test_read_kpoints_from_running_log(self):
        fn = self.testfiles / 'lcao-symm0-nspin2-multik-cellrelax_'
        kpoints = read_kpoints_from_running_log(fn)
        self.assertIsInstance(kpoints, tuple)
        self.assertEqual(len(kpoints), 5)
        # thus we unpack
        kibz, kdspnls, kd1traj, kctraj, kd2traj = kpoints

        # kibz
        self.assertIsInstance(kibz, tuple)
        self.assertEqual(len(kibz), 3)
        # thus we unpack
        kibz, wk, ibz2bz = kibz
        self.assertIsInstance(kibz, np.ndarray)
        self.assertEqual(kibz.shape, (2, 3))
        self.assertIsInstance(wk, np.ndarray)
        self.assertEqual(wk.shape, (2,))
        self.assertAlmostEqual(wk.sum(), 1.0, delta=1e-3)
        self.assertIsInstance(ibz2bz, list)
        self.assertEqual(len(ibz2bz), 2)

        # kdspnls
        self.assertIsInstance(kdspnls, tuple)
        self.assertEqual(len(kdspnls), 2)
        # thus we unpack
        kdspnls, wk = kdspnls
        self.assertIsInstance(kdspnls, np.ndarray)
        self.assertEqual(kdspnls.shape, (2, 3))
        self.assertIsInstance(wk, np.ndarray)
        self.assertEqual(wk.shape, (2,))
        self.assertAlmostEqual(wk.sum(), 1.0, delta=1e-3)

        # kd1traj
        self.assertIsInstance(kd1traj, list)
        self.assertEqual(len(kd1traj), 2) # 2 cell-relax steps
        for i, kd1 in enumerate(kd1traj):
            # because the i=0 corresponds to the spinless case,
            # it has 29 instead of 58 kpoints like the others
            nk = 2
            nspin = 1 if i == 0 else 2
            wktot = 1 if i == 0 else 2
            self.assertIsInstance(kd1, tuple)
            self.assertEqual(len(kd1), 2)
            # thus we unpack
            kd1, wk = kd1
            self.assertIsInstance(kd1, np.ndarray)
            self.assertEqual(kd1.shape, (nspin, nk, 3))
            self.assertIsInstance(wk, np.ndarray)
            self.assertEqual(wk.shape, (nspin, nk))
            self.assertAlmostEqual(wk.sum(), wktot, delta=1e-3)

        # kctraj and kd2traj
        for ktraj in [kctraj, kd2traj]:
            self.assertIsInstance(ktraj, list)
            self.assertEqual(len(ktraj), 2) # 2 cell-relax steps
            for i, k in enumerate(ktraj):
                self.assertIsInstance(k, tuple)
                self.assertEqual(len(k), 2)
                # thus we unpack
                k, wk = k
                self.assertIsInstance(k, np.ndarray)
                self.assertEqual(k.shape, (2, 2, 3))
                self.assertIsInstance(wk, np.ndarray)
                self.assertEqual(wk.shape, (2, 2))
                self.assertAlmostEqual(wk.sum(), 2.0, delta=1e-3)

    def test_read_magmom_from_running_log(self):
        fn = self.testfiles / 'lcao-symm0-nspin2-multik-cellrelax_'
        magmoms = read_magmom_from_running_log(fn)
        self.assertIsInstance(magmoms, list)
        self.assertEqual(len(magmoms), 2) # 2 cell-relax steps
        for i, magmom in enumerate(magmoms):
            self.assertIsInstance(magmom, np.ndarray)
            self.assertEqual(magmom.shape, (4,))
            self.assertAlmostEqual(magmom.sum(), 0.0, delta=1e-3) # AFM

        # non-colinear case
        fn = self.testfiles / 'pw-symm0-nspin4-gamma-md_'
        magmoms = read_magmom_from_running_log(fn)
        self.assertIsInstance(magmoms, list)
        self.assertEqual(len(magmoms), 2)
        for magmom in magmoms:
            self.assertTrue(
                np.allclose(magmom,
                            np.array([[0.        , 0.        , 3.62032142],
                                      [0.        , 0.        , 3.62032142]])))

    def test_read_iter_header_from_running_log(self):
        fn = self.testfiles / 'lcao-symm0-nspin2-multik-cellrelax_'
        header = read_iter_header_from_running_log(fn)
        self.assertEqual(header[0], (1,1))
        self.assertEqual(header[1], (1,2))
        self.assertEqual(header[2], (2,1))
        fn = self.testfiles / 'pw-symm0-nspin4-gamma-md_'
        header = read_iter_header_from_running_log(fn)
        # LTS prints the first and last steps with padding, but ION=2 and
        # ION=3 can be unpadded; neither electronic step may be dropped.
        self.assertEqual(header, [(1, 1), (1, 2), (1, 3),
                                  (2, 1), (3, 1), (3, 2), (3, 3)])

    def test_find_final_info_with_iter_header(self):
        info = [1, 2, 3, 4, 5, 6]
        header = [[1,1], [1,2], [2,1], [3,1], [3,2], [3,3]]
        final_info = find_final_info_with_iter_header(info, header)
        self.assertListEqual(final_info, [info[1], info[2], info[5]])
