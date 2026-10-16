# Tests extracted without semantic changes from the attributed upstream snapshot.
import json
import os
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Optional, List
import numpy as np
from ase.calculators.genericfileio import (
    BaseProfile,
    CalculatorTemplate,
    GenericFileIOCalculator,
    read_stdout
)
from ase.calculators.socketio import SocketIOCalculator
from ase.atoms import Atoms
from ase.dft.kpoints import BandPath
from ase.io import read
from abacuslite.io.generalio import (
    file_safe_backup,
    read_input,
    read_stru,
    read_kpt,
    species_group_indices,
    write_input,
    write_stru,
    write_kpt
)

from abacuslite.core import (switch_io_backend_version, AbacusProfile, AbacusTemplate, Abacus, AbacusSocketIO, __LEGACYIO__)

class TestAbacusCalculator(unittest.TestCase):

    here = Path(__file__).resolve().parents[1] / 'fixtures/io'
    pporb = Path(os.environ.get('ABACUS_PP_ORB', 'missing-PP_ORB'))

    def test_socketio_species_order_mapping(self):
        atoms = Atoms(symbols=['Si', 'O', 'C', 'Si', 'O', 'C'])
        order = AbacusSocketIO._socket_sort_indices(atoms)
        self.assertEqual(order, [0, 3, 1, 4, 2, 5])

        socket_forces = np.arange(18).reshape(6, 3)
        input_forces = AbacusSocketIO._forces_to_input_order(
            socket_forces, order)

        expected = np.empty_like(socket_forces)
        for sorted_index, original_index in enumerate(order):
            expected[original_index] = socket_forces[sorted_index]
        np.testing.assert_array_equal(input_forces, expected)

    def test_socketio_rejects_parameter_changes(self):
        calc = object.__new__(AbacusSocketIO)
        with self.assertRaisesRegex(ValueError, 'fixed after construction'):
            calc.set(kpts={'mode': 'mp-sampling', 'nk': [2, 2, 2]})

    def test_socketio_rejects_cell_changes(self):
        from ase.calculators.calculator import PropertyNotImplementedError

        calc = object.__new__(AbacusSocketIO)
        calc.atoms = Atoms('Si', cell=[5.0, 5.0, 5.0], pbc=True)
        calc._reference_cell = calc.atoms.cell.array.copy()

        changed = calc.atoms.copy()
        changed.cell[0, 0] = 5.1
        with self.assertRaisesRegex(PropertyNotImplementedError, 'fixed-cell'):
            calc._check_fixed_cell(changed)

    def test_socketio_input_keeps_independent_property_switches(self):
        self.assertEqual(
            AbacusSocketIO._socket_inp({'cal_force': 0, 'cal_stress': 1}),
            {'calculation': 'scf', 'socket_driver': 1,
             'cal_force': 0, 'cal_stress': 1})

    def test_socketio_boolean_parser_rejects_ambiguous_values(self):
        for value in ('yes', 'no', 'on', 'off', ''):
            with self.assertRaisesRegex(ValueError, 'cal_force'):
                AbacusSocketIO._input_bool(value, 'cal_force')

    def test_socketio_metadata_rejects_unknown_property(self):
        metadata = json.dumps({
            'schema': 'abacus.socket.properties.v1',
            'present': ['energy', 'charges'],
            'scf_converged': True,
        }).encode('utf-8')
        with self.assertRaisesRegex(ValueError, 'unknown property'):
            AbacusSocketIO._decode_socket_metadata(
                np.frombuffer(metadata, dtype=np.int8))

    def test_socketio_metadata_marks_padding_absent(self):
        metadata = json.dumps({
            'schema': 'abacus.socket.properties.v1',
            'present': ['energy'],
            'scf_converged': False,
        }).encode('utf-8')
        decoded = AbacusSocketIO._decode_socket_metadata(
            np.frombuffer(metadata, dtype=np.int8))
        self.assertEqual(decoded['present'], ('energy',))
        self.assertFalse(decoded['scf_converged'])

    def test_socketio_legacy_response_cannot_infer_force_from_padding(self):
        class LegacyServer:
            def calculate(self, atoms):
                return {
                    'energy': 1.0,
                    'forces': np.zeros((len(atoms), 3)),
                    'virial': np.zeros((3, 3)),
                    'morebytes': b'',
                }

        calc = object.__new__(AbacusSocketIO)
        calc.variable_cell = False
        calc._property_constraints = {}
        calc._active_properties = ('energy', 'forces')
        calc._reference_cell = None
        calc.atoms = None
        calc.server = LegacyServer()
        atoms = Atoms('Si')
        with self.assertRaisesRegex(ValueError, 'refusing to infer forces'):
            calc.calculate(atoms=atoms, properties=('forces',), system_changes=())

    def test_socketio_failed_response_clears_previous_frame(self):
        class BrokenServer:
            def calculate(self, atoms):
                raise EOFError('incomplete frame')

        calc = object.__new__(AbacusSocketIO)
        calc._property_constraints = {}
        calc._active_properties = ('energy',)
        calc._reference_cell = None
        calc.atoms = None
        calc.results = {'energy': 123.0}
        calc.last_scf_converged = True
        calc._last_socket_metadata = {'scf_converged': True}
        calc.server = BrokenServer()
        with self.assertRaises(EOFError):
            calc.calculate(Atoms('Si'), properties=('energy',), system_changes=())
        self.assertEqual(calc.results, {})
        self.assertIsNone(calc.last_scf_converged)
        self.assertIsNone(calc._last_socket_metadata)

    def test_socketio_requested_disabled_property_is_rejected(self):
        calc = object.__new__(AbacusSocketIO)
        calc._property_constraints = {'forces': False, 'stress': False}
        from ase.calculators.calculator import PropertyNotImplementedError
        with self.assertRaises(PropertyNotImplementedError):
            calc._check_requested_properties(('forces',))

    def test_parse_version_allows_launcher_noise(self):
        stdout = 'launcher info\nABACUS version v3.11.0-beta6\n'
        self.assertEqual(AbacusProfile.parse_version(stdout), 'v3.11.0-beta6')

    def test_parse_version_rejects_missing_version(self):
        with self.assertRaisesRegex(RuntimeError, 'ABACUS version'):
            AbacusProfile.parse_version('launcher failed before abacus started')

    def test_calculator_results(self):
        from ase.build.bulk import bulk
        silicon = bulk('Si', crystalstructure='diamond', a=5.43)
        aprof = AbacusProfile(
            command=os.environ.get('ABACUS_COMMAND', 'abacus'),
            pseudo_dir=self.pporb,
            orbital_dir=self.pporb,
            omp_num_threads=1
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            calculator = Abacus(aprof,
                                directory=tmpdir,
                                pseudopotentials={'Si': 'Si_ONCV_PBE-1.0.upf'},
                                basissets={'Si': 'Si_gga_6au_100Ry_2s2p1d.orb'},
                                inp={'calculation': 'scf',
                                    'basis_type': 'lcao',
                                    'ks_solver': 'genelpa',
                                    'ecutwfc': 40,
                                    'symmetry': 1,
                                    'nspin': 1,
                                    'gamma_only': True,
                                    'cal_force': 1,
                                    'cal_stress': 1})
            silicon.calc = calculator
            e = silicon.get_potential_energy()

        # check!
        self.assertAlmostEqual(e, -194.953050937)
        self.assertIsNotNone(calculator.results)
        self.assertIsInstance(calculator.results, dict)
        for k in ['nspins', 'nkpts', 'nbands', 'eigenvalues', 'occupations',
                  'fermi_level', 'kpoint_weights', 'ibz_kpoints', 'energy',
                  'free_energy', 'natoms', 'forces', 'stress', 'magmoms']:
            self.assertIn(k, calculator.results)
        self.assertEqual(calculator.results['nspins'], 1)
        self.assertEqual(calculator.results['nkpts'], 1)
        self.assertEqual(calculator.results['nbands'], 14)
        self.assertEqual(calculator.results['energy'], e)
        self.assertEqual(calculator.results['free_energy'], e)
        self.assertEqual(calculator.results['natoms'], 2)

        for k in ['eigenvalues', 'occupations', 'ibz_kpoints', 'forces', 'stress', 'magmoms']:
            self.assertIsInstance(calculator.results[k], np.ndarray)

        self.assertEqual(calculator.results['eigenvalues'].shape, (1, 1, 14))
        ekb = [-4.82194,  7.62727,  7.62727,  7.62737, 10.2436 , 10.2436 ,
                10.2436 , 10.9884 , 16.057  , 16.057  , 23.8353 , 25.421  ,
                25.421  , 25.4212 ]
        self.assertTrue(np.allclose(calculator.results['eigenvalues'][0, 0, :], np.array(ekb)))

        self.assertEqual(calculator.results['occupations'].shape, (1, 1, 14))
        occ = [2., 2., 2., 2., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
        self.assertTrue(np.allclose(calculator.results['occupations'][0, 0, :], np.array(occ)))

        self.assertEqual(calculator.results['ibz_kpoints'].shape, (1, 3))
        self.assertTrue(np.allclose(calculator.results['ibz_kpoints'][0, :], np.array([0,0,0])))

        self.assertEqual(calculator.results['forces'].shape, (2, 3))
        self.assertTrue(np.allclose(calculator.results['forces'], np.zeros((2, 3))))

        self.assertEqual(calculator.results['stress'].shape, (6,))
        stress = [-0.19327923, -0.19327923, -0.19327923, -0.        ,  0.        ,   0.        ]
        self.assertTrue(np.allclose(calculator.results['stress'], np.array(stress)))

        self.assertEqual(calculator.results['magmoms'].shape, (2,))
        self.assertTrue(np.allclose(calculator.results['magmoms'], np.zeros(2)))

    def test_restart(self):
        from ase.build.bulk import bulk
        silicon = bulk('Si', crystalstructure='diamond', a=5.43)
        aprof = AbacusProfile(
            command=os.environ.get('ABACUS_COMMAND', 'abacus'),
            pseudo_dir=self.pporb,
            orbital_dir=self.pporb,
            omp_num_threads=1
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            calculator = Abacus(aprof,
                                directory=tmpdir,
                                pseudopotentials={'Si': 'Si_ONCV_PBE-1.0.upf'},
                                basissets={'Si': 'Si_gga_6au_100Ry_2s2p1d.orb'},
                                inp={'calculation': 'scf',
                                    'basis_type': 'lcao',
                                    'ks_solver': 'genelpa',
                                    'ecutwfc': 40,
                                    'symmetry': 1,
                                    'nspin': 1,
                                    'gamma_only': True,
                                    'cal_force': 1,
                                    'cal_stress': 1})
            silicon.calc = calculator
            e = silicon.get_potential_energy()

            # restart
            silicon.calc = Abacus.restart(aprof, directory=tmpdir)
            e2 = silicon.get_potential_energy()
            self.assertAlmostEqual(e2, e)

    def test_version_number_check(self):
        # not a version number
        with self.assertRaises(AssertionError):
            switch_io_backend_version('not-a-version-number')
        # too old version
        with self.assertRaises(AssertionError):
            switch_io_backend_version('v2.2.2')
        self.assertTrue(switch_io_backend_version('v3.8.4'))
        self.assertFalse(switch_io_backend_version('v3.9.0.25'))
        self.assertTrue(switch_io_backend_version('v3.10.0'))
        self.assertFalse(switch_io_backend_version('v3.11.0-beta.2'))
        self.assertFalse(switch_io_backend_version('v3.11.0'))

    def test_property_keywords_reject_conflicting_user_parameters(self):
        template = AbacusTemplate()
        with self.assertRaises(ValueError):
            template.get_property_keywords({'nspin': 1}, ['magmom'])

        parameters = template.get_property_keywords({'nspin': 2}, ['magmom'])
        self.assertEqual(str(parameters['nspin']), '2')

    def test_property_keywords_accept_equivalent_boolean_user_parameters(self):
        template = AbacusTemplate()

        parameters = template.get_property_keywords(
            {'cal_force': True, 'cal_stress': True},
            ['forces', 'stress']
        )

        self.assertEqual(str(parameters['cal_force']), '1')
        self.assertEqual(str(parameters['cal_stress']), '1')

    def test_property_keywords_reject_conflicting_boolean_user_parameters(self):
        template = AbacusTemplate()

        with self.assertRaises(ValueError):
            template.get_property_keywords({'cal_force': False}, ['forces'])

        with self.assertRaises(ValueError):
            template.get_property_keywords({'cal_stress': False}, ['stress'])

    def test_property_keywords_treat_string_values_as_scalars(self):
        template = AbacusTemplate()
        template.implemented_properties = ['probe']
        template.get_probe_keywords = lambda parameters: {'custom_switch': 'true'}

        parameters = template.get_property_keywords(
            {'custom_switch': 'true'}, ['probe']
        )

        self.assertEqual(parameters['custom_switch'], 'true')

    def test_property_keywords_compare_iterables_like_input_writer(self):
        template = AbacusTemplate()
        template.implemented_properties = ['probe']
        template.get_probe_keywords = lambda parameters: {
            'custom_vector': [1, 'true']
        }

        with self.assertRaises(ValueError):
            template.get_property_keywords(
                {'custom_vector': [True, 'true']}, ['probe']
            )

    def test_property_keywords_reject_conflicting_properties(self):
        template = AbacusTemplate()
        template.implemented_properties = ['prop_a', 'prop_b']
        template.get_prop_a_keywords = lambda parameters: {'calculation': 'scf'}
        template.get_prop_b_keywords = lambda parameters: {'calculation': 'md'}

        with self.assertRaises(ValueError):
            template.get_property_keywords({}, ['prop_a', 'prop_b'])

    def test_dipole_property_is_not_implemented(self):
        template = AbacusTemplate()
        self.assertNotIn('dipole', template.implemented_properties)
        with self.assertRaises(AssertionError):
            template.get_property_keywords({}, ['dipole'])
