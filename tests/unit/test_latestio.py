# Tests extracted without semantic changes from the attributed upstream snapshot.
import re
import shutil
import unittest
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
from ase.atoms import Atoms
from ase.calculators.singlepoint import (
    SinglePointKPoint,
    SinglePointDFTCalculator
)
from ase.units import GPa
from ase.stress import full_3x3_to_voigt_6_stress
from abacuslite.io.legacyio import (
    read_kpoints_from_running_log,
    read_energies_from_running_log,
    read_traj_from_md_dump,
    read_magmom_from_running_log,
    is_invalid_arr,
    find_final_info_with_iter_header
)

from abacuslite.io.latestio import (read_esolver_type_from_running_log, read_band_from_running_log, read_band_from_eig_occ, read_traj_from_running_log, read_forces_from_running_log, read_stress_from_running_log, read_iter_header_from_running_log, read_abacus_out)

class TestLatestIO(unittest.TestCase):
    '''
    test the validities of functions for the I/O of the latest version of ABACUS
    '''
    here = Path(__file__).resolve().parents[1] / 'fixtures/io'
    testfiles = here / 'testfiles'

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

        with tempfile.TemporaryDirectory() as tmpdir:
            running_log = Path(tmpdir) / 'running_scf.log'
            running_log.write_text('')
            (Path(tmpdir) / 'eig_occ.txt').write_text('')
            with patch('abacuslite.io.latestio' + '.read_esolver_type_from_running_log', return_value='ksdft'), \
                 patch('abacuslite.io.latestio' + '.read_traj_from_running_log', return_value=[frame]), \
                 patch('abacuslite.io.latestio' + '.read_band_from_eig_occ', return_value=elecstate), \
                 patch('abacuslite.io.latestio' + '.read_forces_from_running_log', return_value=[]), \
                 patch('abacuslite.io.latestio' + '.read_stress_from_running_log', return_value=[]), \
                 patch('abacuslite.io.latestio' + '.read_kpoints_from_running_log', return_value=kpoints), \
                 patch('abacuslite.io.latestio' + '.read_energies_from_running_log', return_value=([], [])), \
                 patch('abacuslite.io.latestio' + '.read_iter_header_from_running_log', return_value=[]), \
                 patch('abacuslite.io.latestio' + '.find_final_info_with_iter_header', return_value=energies), \
                 patch('abacuslite.io.latestio' + '.read_magmom_from_running_log', return_value=[np.array([10.0, 20.0, 30.0])]):
                atoms = read_abacus_out(running_log, sort_atoms_with=[0, 2, 1])[0]

        self.assertEqual(atoms.get_chemical_symbols(), ['Na', 'Cl', 'Na'])
        self.assertTrue(np.allclose(atoms.cell.array, np.eye(3)))
        self.assertFalse(np.any(atoms.pbc))
        self.assertTrue(np.allclose(atoms.calc.results['magmoms'], [10.0, 30.0, 20.0]))

    def test_read_abacus_out_exposes_entropy_corrected_energy(self):
        """Expose E_KohnSham and the entropy-corrected free energy."""
        fixture = Path(__file__).resolve().parents[1] / 'fixtures' / 'multiframe_md_latest'
        frames = read_abacus_out(fixture / 'running_md.log')
        last = frames[-1]

        self.assertAlmostEqual(last.get_potential_energy(), -1940.6311063727, delta=1e-9)
        self.assertAlmostEqual(
            last.get_potential_energy(force_consistent=True),
            -1940.4234898941,
            delta=1e-9,
        )

    def test_native_md_dump_cell_units_at_atoms_boundary(self):
        """MD_dump vectors are in alat; positions and energies are already physical."""
        fixture = Path(__file__).resolve().parents[1] / 'fixtures' / 'multiframe_md_latest'
        dump = fixture / 'MD_dump'
        log = fixture / 'running_md.log'
        before = {path.name: path.read_bytes() for path in fixture.iterdir()}

        raw = read_traj_from_md_dump(dump)
        self.assertEqual(len(raw), 2)
        self.assertEqual(raw[0]['alat_in_angstrom'], 0.529177)
        self.assertEqual(raw[0]['coordinate'], 'Cartesian')
        self.assertTrue(np.allclose(raw[0]['cell'][0], [5.34197, 5.34197, 0.0], atol=1e-12))
        self.assertTrue(np.allclose(raw[0]['coords'][0],
                                    [1.413423737926] * 3, atol=1e-12))

        frames = read_abacus_out(log)
        self.assertEqual(len(frames), 2)
        expected_cell = np.array([[2.82684765869, 2.82684765869, 0.0],
                                  [0.0, 2.82684765869, 2.82684765869],
                                  [2.82684765869, 0.0, 2.82684765869]])
        expected_positions = [
            [[1.413423737926] * 3, [0.0, 0.0, 0.0]],
            [[1.413423737926] * 3,
             [0.025620321279, 2.822443204757, 2.834296002714]],
        ]
        expected_energies = [-1940.6273962477, -1940.6311063727]
        for atoms, positions, energy in zip(frames, expected_positions, expected_energies):
            self.assertTrue(np.all(atoms.pbc))
            self.assertTrue(np.allclose(atoms.cell.array, expected_cell, atol=1e-10))
            self.assertAlmostEqual(atoms.get_volume(), 45.1791, delta=1e-4)
            self.assertTrue(np.allclose(atoms.positions, positions, atol=1e-12))
            self.assertAlmostEqual(atoms.get_potential_energy(), energy, delta=1e-9)
        self.assertEqual(before, {path.name: path.read_bytes() for path in fixture.iterdir()})

    def test_read_esolver_type_from_running_log(self):
        self.assertEqual(
            read_esolver_type_from_running_log(
                self.testfiles / 'lcao-symm0-nspin2-multik-cellrelax'),
            'ksdft_lcao'
        )
        self.assertEqual(
            read_esolver_type_from_running_log(
                self.testfiles / 'lcao-symm0-nspin2-multik-relax'),
            'ksdft_lcao'
        )
        self.assertEqual(
            read_esolver_type_from_running_log(
                self.testfiles / 'lcao-symm1-nspin1-multik-scf'),
            'ksdft_lcao'
        )
        self.assertEqual(
            read_esolver_type_from_running_log(
                self.testfiles / 'pw-symm0-nspin4-gamma-md'),
            'ksdft_pw'
        )

    def test_read_band_from_running_log(self):
        self.assertIsNone(
            read_band_from_running_log(self.testfiles / 'lcao-symm0-nspin2-multik-cellrelax')
        )

    def test_read_band_from_eig_occ(self):
        fn = self.testfiles / 'nspin4-gamma-eigocc'
        elecstate = read_band_from_eig_occ(fn)
        # 2 frames, 1 spin channel (nspin 4), 1 kpoint, 35 bands
        self.assertEqual(len(elecstate), 2)
        for es in elecstate: # loop over frames
            self.assertIn('k', es)
            self.assertEqual(es['k'].shape, (1, 1, 3)) # ispin, ik, 3
            self.assertIn('e', es)
            self.assertEqual(es['e'].shape, (1, 1, 35)) # ispin, ik, nbnd
            self.assertIn('occ', es)
            self.assertEqual(es['occ'].shape, (1, 1, 35)) # ispin, ik, nbnd

    def test_read_traj_from_running_log(self):
        traj = read_traj_from_running_log(self.testfiles / 'lcao-symm0-nspin2-multik-cellrelax')
        self.assertEqual(len(traj), 3)

        reference = [
            np.array([[4.17203 , 2.086015, 2.086015],
                      [2.086015, 4.17203 , 2.086015],
                      [2.086015, 2.086015, 4.17203 ]]),
            np.array([[4.17550947, 2.05376104, 2.05376104],
                      [2.05811246, 4.12078078, 2.09979522],
                      [2.05811246, 2.09979522, 4.12078078]]),
            np.array([[4.17667347, 2.04296382, 2.04296382],
                      [2.04876712, 4.10361705, 2.10440948],
                      [2.04876712, 2.10440948, 4.10361705]])
        ]

        taud = np.array([[0.  , 1.  , 1.  ],
                         [0.5 , 0.5 , 0.5 ],
                         [0.25, 0.25, 0.25],
                         [0.75, 0.75, 0.75]])
        for t, c in zip(traj, reference):
            self.assertEqual(t['coordinate'], 'Direct')
            self.assertEqual(t['cell_unit'], 'Angstrom'),
            self.assertEqual(t['alat_in_angstrom'], 4.17203)
            self.assertTrue(all(e1 == e2 for e1, e2 in zip(t['elem'], np.array(['Ni1', 'Ni2', 'O', 'O']))))
            self.assertTrue(np.allclose(t['cell'], c))
            self.assertTrue(np.allclose(t['coords'] % 1, taud % 1))

    def test_read_forces_from_running_log(self):
        forces = read_forces_from_running_log(self.testfiles / 'lcao-symm0-nspin2-multik-relax')
        self.assertEqual(len(forces), 2) # two frames
        reference = [
            np.array([
                [-1.2994798821, -0.7502719805, 0.0000000000],
                [ 1.2994798821,  0.7502719805, 0.0000000000],
            ]),
            np.array([
                [-1.6814741322, -0.9708025265, 0.0000000000],
                [ 1.6814741322,  0.9708025265, 0.0000000000],
            ]),
        ]
        for f, ref in zip(forces, reference):
            self.assertTrue(np.allclose(f, ref))

    def test_read_stress_from_running_log(self):
        stresses = read_stress_from_running_log(
            self.testfiles / 'lcao-symm0-nspin2-multik-cellrelax')
        self.assertEqual(len(stresses), 2) # two frames
        reference = [
            np.array([
               [ 28.0257165781, -25.0814687477, -25.0814687477],
               [-25.0814687477, -57.2309475134,  52.8147857580],
               [-25.0814687477,  52.8147857580, -57.2309475134],
            ]),
            np.array([
                [ 10.5133147463,-28.8166870580, -28.8166870559],
                [-28.8166870580,  0.1640200010,   7.6016822662],
                [-28.8166870559,  7.6016822662,   0.1640199977],
            ]),
        ]
        for s, ref in zip(stresses, reference):
            self.assertTrue(np.allclose(s, -0.1 * GPa * ref))

    def test_read_abacus_out_string(self):
        fn = self.testfiles / 'pw-symm0-nspin4-gamma-md'
        # the case that does not give the instance of Path
        with self.assertRaises(AssertionError):
            read_abacus_out(str(fn))

    def test_read_pw_symm0_nspin4_gamma_md(self):
        # make files ready
        shutil.copy(self.testfiles / 'pw-symm0-nspin4-gamma-md',
                    self.testfiles / 'running_md.log')
        shutil.copy(self.testfiles / 'nspin4-gamma-eigocc',
                    self.testfiles / 'eig_occ.txt')
        shutil.copy(self.testfiles / 'nspin4-gamma-mddump',
                    self.testfiles / 'MD_dump')

        res = read_abacus_out(self.testfiles / 'running_md.log')
        self.assertIsNotNone(res)
        self.assertEqual(len(res), 2) # two frames

        for atoms in res:
            self.assertIsInstance(atoms, Atoms)
            self.assertIsInstance(atoms.calc, SinglePointDFTCalculator)
            self.assertGreater(len(atoms.calc.kpts), 0)
            # Gamma point calculation
            for k in atoms.calc.kpts:
                self.assertIsInstance(k, SinglePointKPoint)

        # remove the files
        (self.testfiles / 'running_md.log').unlink()
        (self.testfiles / 'eig_occ.txt').unlink()
        (self.testfiles / 'MD_dump').unlink()

    def test_read_iter_header_from_running_log(self):
        header = read_iter_header_from_running_log(
            self.testfiles / 'lcao-symm0-nspin2-multik-cellrelax')
        self.assertTupleEqual(header[0], (1, 1))
        self.assertTupleEqual(header[1], (1, 2))
        self.assertTupleEqual(header[2], (2, 1))
