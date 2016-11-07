#! /usr/bin/env python

import os
import shutil
import unittest

import mock

from tutils import local_pythonpath, get_local_path

# Setup project-local PYTHONPATH
local_pythonpath('..', '..', 'src')

import utils
import decompressor

_TEST_FILES = ['random_1M_bz2.bin.bz2', 'random_1M_gz.bin.gz',
               'random_1M_zip.bin.zip', 'random_2files_zip.bin.zip']

class DecompressorSimpleTest(unittest.TestCase):

    testdir = '/tmp/TestDecompressorSimple'

    def setUp(self): # pragma: no cover
        if os.path.exists(self.testdir):
            shutil.rmtree(self.testdir)
        os.mkdir(self.testdir)
        for fn in _TEST_FILES:
            local_path = get_local_path('..', 'data', fn)
            shutil.copy(local_path, self.testdir)

    def tearDown(self): # pragma: no cover
        shutil.rmtree(self.testdir)

    def test_decompressor_simple(self):
        for fn in _TEST_FILES:
            local_path = os.path.join(self.testdir, fn)
            d = decompressor.Decompressor(local_path)
            self.assertTrue(d.doit())
            name, _ = os.path.splitext(local_path)
            self.assertTrue(os.path.exists(name))
            self.assertTrue(os.path.exists(local_path))

    def test_decompressor_simple_delete(self):
        for fn in _TEST_FILES:
            local_path = os.path.join(self.testdir, fn)
            d = decompressor.Decompressor(local_path)
            self.assertTrue(d.doit(delete=True))
            name, _ = os.path.splitext(local_path)
            self.assertTrue(os.path.exists(name))
            self.assertFalse(os.path.exists(local_path))

    def test_decompressor_main(self):
        test_files = [os.path.join(self.testdir, fn) for fn in _TEST_FILES]
        self.assertTrue(decompressor.main(test_files))

    def test_decompressor_ioerror(self):
        fn = os.path.join(self.testdir, _TEST_FILES[0])
        d = decompressor.Decompressor(fn)
        with mock.patch('utils.block_read_filedesc',
                        mock.Mock(side_effect=IOError('Boom!'))):
            self.assertFalse(d.doit()[0])
            self.assertTrue(os.path.exists(fn))
        with mock.patch('utils.block_read_filedesc',
                        mock.Mock(side_effect=IOError('Not a gzipped file'))):
            self.assertFalse(d.doit()[0])
            self.assertTrue(os.path.exists(fn))
        with mock.patch('utils.block_read_filedesc',
                        mock.Mock(side_effect=IOError('Not a gzipped file'))):
            self.assertFalse(d.doit(True)[0])
            self.assertTrue(os.path.exists(fn))

class DecompressorErrorsTest(unittest.TestCase):

    def test_decompressor_good_ext_devnull(self):
        for ext in decompressor._EXT_MAP:
            d = decompressor.Decompressor(os.devnull, ext)
            ret, fn = d.doit()
            self.assertFalse(ret)
            self.assertEqual(fn, os.devnull + '_uncompressed')

    def test_decompressor_good_ext_existent(self):
        fn = '/tmp/' + utils.test_name() + '.ext'
        open(fn, 'wb+').close()
        with self.assertRaises(decompressor.DecompressorError):
            decompressor.Decompressor(fn)
        with self.assertRaises(decompressor.DecompressorError):
            decompressor.Decompressor(fn, '.zip')

    def test_decompressor_no_ext_existent(self):
        fn = '/tmp/' + utils.test_name()
        open(fn, 'wb+').close()
        with self.assertRaises(decompressor.DecompressorError):
            decompressor.Decompressor(fn)
        open(fn + '.zip', 'wb+').close()
        with self.assertRaises(decompressor.DecompressorError):
            decompressor.Decompressor(fn + '.zip')

    def test_decompressor_good_ext_not_existent(self):
        for ext in decompressor._EXT_MAP:
            with self.assertRaises(decompressor.DecompressorError):
                decompressor.Decompressor('/tmp/nonexistent', ext)
            with self.assertRaises(decompressor.DecompressorError):
                decompressor.Decompressor('/tmp/nonexistent' + ext)

    def test_decompressor_bad_ext_param(self):
        with self.assertRaises(decompressor.DecompressorError):
            decompressor.Decompressor(os.devnull, '.txt')

    def test_decompressor_bad_ext(self):
        with self.assertRaises(decompressor.DecompressorError):
            decompressor.Decompressor('/tmp/nonexistent.txt')

    def test_decompressor_nonexistent(self):
        with self.assertRaises(decompressor.DecompressorError):
            decompressor.Decompressor('/tmp/nonexistent')

if __name__ == '__main__': # pragma: no cover
    import pytest
    pytest.main(['-x', '--pdb', __file__])
