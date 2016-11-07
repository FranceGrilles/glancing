#! /usr/bin/env python

import sys
import unittest

import tutils

class TutilsTest(unittest.TestCase):

    def test_tutils_mod_path(self):
        self.assertTrue(tutils.mod_path().endswith('/glancing/test/src'))

    def test_tutils_get_local_path(self):
        lp = tutils.get_local_path('toto', 'titi.txt')
        self.assertTrue(lp.endswith('/glancing/test/src/toto/titi.txt'))

    def test_tutils_local_pythonpath(self):
        def count_endswith(alist, suffix):
            return len([x for x in alist if x.endswith(suffix)])
        self.assertEqual(0, count_endswith(sys.path, 'TOTO'))
        tutils.local_pythonpath('TOTO')
        self.assertEqual(1, count_endswith(sys.path, 'TOTO'))
        tutils.local_pythonpath('TOTO')
        self.assertEqual(1, count_endswith(sys.path, 'TOTO'))
        sys.path.remove(tutils.get_local_path('TOTO'))
        self.assertEqual(0, count_endswith(sys.path, 'TOTO'))
