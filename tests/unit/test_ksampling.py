# Tests extracted without semantic changes from the attributed upstream snapshot.
import seekpath
import unittest
from typing import Optional, Tuple, List, Dict
import numpy as np
from ase.atoms import Atoms

from abacuslite.utils.ksampling import (convert_kspacing_to_kpts, get_kpath, interpolate_kpath, merge_ksgm, make_kstring, make_klines, kpathgen, SILICON_KNODES, SILICON_KNAMES, SILICON_NINTPL)

class TestKsampling(unittest.TestCase):

    def test_convert_kspacing(self):
        # test-reference: ABACUS 3.8.4 implementation
        from ase.geometry import cellpar_to_cell

        cell = cellpar_to_cell([4.22798145, 4.22798145, 4.22798145, 60, 60, 60])
        kpts = convert_kspacing_to_kpts(cell, 0.03*1.889725989)
        # kspacing 0.03 Bohr-1, multiply 1.889725989 to convert to Angstrom-1
        self.assertEqual(kpts, (33, 33, 33))

    def test_merge_ksgm(self):
        klables, is_brkpt = merge_ksgm([('GAMMA', 'X'), ('X', 'U'), ('K', 'GAMMA'),
                                        ('GAMMA', 'L'), ('L', 'W'), ('W', 'X')])
        self.assertEqual(klables, ['GAMMA',  'X',  'U',   'K','GAMMA', 'L', 'W', 'X'])
        self.assertEqual(is_brkpt, [False, False, True, False,  False, False, False, True])

    def test_make_kstring(self):
        fklblfilter = lambda lbl: lbl if lbl != 'GAMMA' else 'G'
        klabels = ['GAMMA',  'X',  'U',   'K','GAMMA', 'L', 'W', 'X']
        klabels = [fklblfilter(lbl) for lbl in klabels]
        is_brkpt = [False, False, True, False,  False, False, False, True]
        self.assertEqual(make_kstring(klabels, is_brkpt), 'GXU,KGLWX')
