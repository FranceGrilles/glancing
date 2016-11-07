#! /usr/bin/env python

import os
import sys
import unittest

from functools import wraps

from tutils import local_pythonpath, get_local_path

# Setup project-local PYTHONPATH
local_pythonpath('..', '..', 'src')

import utils
from utils import devnull, environ, test_name, run, cleanup

import glance
import glancing
import multihash

# Check we have a cloud ready to import images into...
_GLANCE_OK = False
with devnull('stderr'):
    _GLANCE_OK = run(['glance', 'image-list'])[0]

# Avoid heavy image download tests
_HEAVY_TESTS = False # < 500 MB images, ~2 min -> ~6 min...
_HUGE_TESTS = False # 1 x 5 GB image

def glance_cleanup(name=None):
    '''Decorator that automagically clean up after a test.
    An image that has the 'name' name is deleted upon test exit.
    If the 'name' parameter is not given, it defaults to the test method name
    itself. And it tests that the image does not exists before exiting the test.
    '''
    def wrapper(f):
        @wraps(f)
        def wrapped(self, *f_args, **f_kwargs):
            with cleanup(glance.glance_delete, name or f.func_name):
                f(self, *f_args, **f_kwargs)
        return wrapped
    return wrapper

class GlancingMiscTest(unittest.TestCase):

    def test_glancing_main_glance_availabilityFail(self):
        with environ('PATH'):
            self.assertFalse(glancing.main([os.devnull]))

    @glance_cleanup('null')
    @unittest.skipUnless(_GLANCE_OK, "glance not properly configured")
    def test_glancing_main_glance_availabilityOK(self):
        self.assertTrue(glancing.main([os.devnull]))

    def test_glancing_empty_cli_param(self):
        self.assertFalse(glancing.main(['']))
        self.assertFalse(glancing.main(['-d', '']))

class GlancingGetUrlTest(unittest.TestCase):

    def test_glancing_get_url(self):
        self.assertIsNone(glancing.get_url(None))
        self.assertIsNone(glancing.get_url(True))
        self.assertIsNone(glancing.get_url(False))
        self.assertIsNone(glancing.get_url([]))
        self.assertIsNone(glancing.get_url(tuple()))
        self.assertIsNone(glancing.get_url(set()))
        self.assertIsNone(glancing.get_url(frozenset))
        self.assertIsNone(glancing.get_url({}))
        self.assertIsNone(glancing.get_url(1))
        self.assertIsNone(glancing.get_url('a'))
        self.assertIsNone(glancing.get_url(u'a'))
        self.assertIsNone(glancing.get_url(''))
        self.assertIsNone(glancing.get_url(u''))
        self.assertIsNone(glancing.get_url(u'http://google.fr/totototo'))

class GlancingImageDryRunNotExistentTest(unittest.TestCase):

    def test_glancing_image_notexistent(self):
        self.assertFalse(glancing.main(['-d', '/notexistent.txt']))

    def test_glancing_image_notexistent_sum(self):
        self.assertFalse(glancing.main(['-d', '/notexistent.txt',
            '-s', '0' * 32]))

class GlancingImageDryRunDevnullTest(unittest.TestCase):

    _DEVNULL_MD5 = 'd41d8cd98f00b204e9800998ecf8427e'

    def test_glancing_image_devnull(self):
        self.assertTrue(glancing.main(['-d', os.devnull]))

    def test_glancing_image_notenough_param(self):
        with devnull('stderr'):
            with self.assertRaises(SystemExit):
                glancing.main(['-d', os.devnull, '-s'])

    def test_glancing_image_devnull_sum_bad(self):
        sums = ['### BAD CHECKSUM ###', '0' * 32, self._DEVNULL_MD5 +
            ':' + '0' * 32]
        for asum in sums:
            self.assertFalse(glancing.main(['-d', os.devnull, '-s', asum]))

    def test_glancing_image_devnull_sum_empty(self):
        self.assertTrue(glancing.main(['-d', os.devnull, '-s', '']))

    def test_glancing_image_devnull_sum(self):
        self.assertTrue(glancing.main(['-d', os.devnull, '-s',
            self._DEVNULL_MD5]))

    def test_glancing_image_devnull_sum_verbose(self):
        self.assertTrue(glancing.main(['-dv', os.devnull, '-s',
            self._DEVNULL_MD5]))

class TestGlancingImageTtylinuxBase(unittest.TestCase):

    _TTYLINUX_FILE = get_local_path('..', 'images', 'ttylinux-16.1-x86_64.img')
    _TTYLINUX_MD5 = '3d1b4804dcf2a613f0ed4a91b9ed2b98'

class GlancingImageDryRunTtylinuxTest(TestGlancingImageTtylinuxBase):

    def test_glancing_image_ttylinux(self):

        md5 = self._TTYLINUX_MD5
        sha1 = '1b5229d5dad92bc7952553be01608af2180eafbe'
        sha512 = ('79556bc3a25e4555a6cd71afba8eae80eb6d5f23f16a84e6' +
                  '017a54469034cf77ee7bcd74ac285c6ec42c25547b6963c1' +
                  'e7232d4fcca388a326f0ec3e7afb838e')

        self.assertTrue(glancing.main(['-d', self._TTYLINUX_FILE]))

        checksums_true = ['', ':', ':::::', sha512, sha1 + ':' + md5,
            md5 + ':', ':' + md5]

        for chks in checksums_true:
            self.assertTrue(glancing.main(['-d',
                self._TTYLINUX_FILE, '-s', chks]), chks)

        checksums_false = ['a' + md5, 'a' + md5 + ':' + md5, md5[:12] +
            '0' + md5[13:], md5 + ':' + md5[:12] + '0' + md5[13:]]

        for chks in checksums_false:
            self.assertFalse(glancing.main(['-d',
                self._TTYLINUX_FILE, '-s', chks]), chks)

class GlancingImageDryRunCoreosTest(unittest.TestCase):

    def test_glancing_image_coreos(self):
        fn = 'coreos_production_qemu_image.img'
        imgfile = get_local_path('..', 'images', fn)
        chksumfile = get_local_path('..', 'images', 'coreos-MD5SUMS')
        with open(chksumfile, 'rb') as fin:
            md5 = fin.read(multihash.hash2len('md5'))
        self.assertTrue(glancing.main(['-v', '-d', imgfile, '-s',
            md5 + ':' + md5]))

class GlancingCirrosImageTest(unittest.TestCase):

    _CIRROS_FILE = get_local_path('..', 'images', 'cirros-0.3.4-i386-disk.img')
    _CIRROS_MD5 = get_local_path('..', 'images', 'cirros-MD5SUMS')
    _CIRROS_SHA1 = get_local_path('..', 'images', 'cirros-SHA1SUMS')
    _CIRROS_CHK = '79b4436412283bb63c2cba4ac796bcd9'

    def test_glancing_file_dryrun_good_sum(self):
        self.assertTrue(glancing.main(['-d', '-n', test_name(),
            self._CIRROS_FILE, '-S', self._CIRROS_MD5]))
        self.assertTrue(glancing.main(['-d', '-n', test_name(),
            self._CIRROS_FILE, '-S', self._CIRROS_SHA1]))
        self.assertTrue(glancing.main(['-d', '-n', test_name(),
            self._CIRROS_FILE, '-S', self._CIRROS_SHA1, '-S', self._CIRROS_MD5]))
        self.assertTrue(glancing.main(['-d', '-n', test_name(),
            self._CIRROS_FILE, '-S', self._CIRROS_MD5, '-s', self._CIRROS_CHK]))
        self.assertTrue(glancing.main(['-d', '-n', test_name(),
            self._CIRROS_FILE, '-s', self._CIRROS_CHK, '-S', self._CIRROS_SHA1]))

    @glance_cleanup()
    @unittest.skipUnless(_GLANCE_OK, "glance not properly configured")
    def test_glancing_file_import_good_sum(self):
        self.assertTrue(glancing.main(['-n', test_name(),
            self._CIRROS_FILE, '-S', self._CIRROS_MD5]))

@unittest.skipUnless(_GLANCE_OK, "glance not properly configured")
class GlancingImageTest(TestGlancingImageTtylinuxBase):

    def test_glancing_image_import_noname(self):
        name, _ = os.path.splitext(os.path.basename(self._TTYLINUX_FILE))
        with cleanup(glance.glance_delete, name):
            self.assertTrue(glancing.main(['-f',
                self._TTYLINUX_FILE, '-s', self._TTYLINUX_MD5]))

    @glance_cleanup()
    def test_glancing_image_import_name(self):
        self.assertTrue(glancing.main(['-n', test_name(),
            self._TTYLINUX_FILE, '-s', self._TTYLINUX_MD5]))

    @glance_cleanup()
    def test_glancing_image_import_name_bad_md5(self):
        self.assertFalse(glancing.main(['-n', test_name(),
            self._TTYLINUX_FILE, '-s', '0' * 32]))

    @glance_cleanup()
    def test_glancing_image_import_name_force(self):
        self.assertTrue(glancing.main(['-f', '-n', test_name(),
            self._TTYLINUX_FILE, '-s', '0' * 32]))

class GlancingMetadataCernTest(unittest.TestCase):

    @glance_cleanup()
    @unittest.skipUnless(_GLANCE_OK, "glance not properly configured")
    def test_glancing_metadata_cern_cirros_import(self):
        # 12 MB
        mdfile = get_local_path('..', 'CERN', 'test_image_list')
        self.assertTrue(glancing.main(['-v', '-n', test_name(), '-c',
            mdfile, '-k', "deadbabe-f00d-beef-cafe-b1ab1ab1a666"]))

class GlancingMetadataTest(unittest.TestCase):

    @unittest.skipUnless(_HEAVY_TESTS, "image too big")
    def test_glancing_metadata_heavies(self):
        market_ids = (
            # 98 MB, size & checksum mismatch: 4 B -> 98 MB
            ('JcqGhHxmTRAEpHMmRF-xhSTM3TO', False, False, False),
            # 102 MB, does not exists any more on SL marketplace
            ('BtSKdXa2SvHlSVTvgFgivIYDq--', True, False, False),
            # 872 MB
            ('IzEOzeHK8-zpgSyAkhNiZujL4nZ', True, True, True),
            # Size & checksum mismatch: 375 MB -> 492 MB
            ('ME4iRTemHRwhABKV5AgrkQfDerA', False, False, False),
        )
        for market_id, status_json, status_xml, status_market in market_ids:
            mdfile_base = get_local_path('..', 'stratuslab', market_id)
            self.assertEqual(status_json, glancing.main(['-d',
                mdfile_base + '.json']), mdfile_base + '.json')
            self.assertEqual(status_xml, glancing.main(['-d',
                mdfile_base + '.xml']), mdfile_base + '.xml')
            self.assertEqual(status_market, glancing.main(['-d',
                market_id]), market_id)

    @glance_cleanup()
    @unittest.skipUnless(_HEAVY_TESTS, "image too big")
    @unittest.skipUnless(_GLANCE_OK, "glance not properly configured")
    def test_glancing_metadata_bad_but_force(self):
        # Size & checksum mismatch: 375 MB -> 492 MB
        market_id = 'ME4iRTemHRwhABKV5AgrkQfDerA'
        mdfile = get_local_path('..', 'stratuslab', market_id + '.json')
        self.assertTrue(glancing.main(['-vf', '-n', test_name(), mdfile]))
        self.assertTrue(glance.glance_delete(test_name()))
        self.assertFalse(glancing.main(['-vf', '-n', test_name(), market_id]))

    @glance_cleanup()
    @unittest.skipUnless(_GLANCE_OK, "glance not properly configured")
    def test_glancing_metadata_cirros_import(self):
        # 12 MB
        mdfile = get_local_path('..', 'stratuslab', 'cirros.json')
        with devnull('stderr'):
            self.assertTrue(glancing.main(['-v', '-n', test_name(),
                mdfile, '-k']))

    @glance_cleanup()
    @unittest.skipUnless(_GLANCE_OK, "glance not properly configured")
    def test_glancing_metadata_cirros_import_no_cksum(self):
        # 12 MB
        mdfile = get_local_path('..', 'stratuslab', 'cirros_no_cksum.json')
        with devnull('stderr'):
            self.assertTrue(glancing.main(['-v', '-n', test_name(),
                mdfile, '-k']))

    @glance_cleanup()
    @unittest.skipUnless(_GLANCE_OK, "glance not properly configured")
    def test_glancing_metadata_cirros_import_bad_size(self):
        # 12 MB
        mdfile = get_local_path('..', 'stratuslab', 'cirros_bad_size.json')
        with devnull('stderr'):
            self.assertFalse(glancing.main(['-v', '-n', test_name(), mdfile]))
            self.assertTrue(glancing.main(['-f', '-n', test_name(), mdfile]))

    @unittest.skipUnless(_HUGE_TESTS, "image too big: 5.0 GB")
    def test_glancing_metadata_big(self):
        market_id = 'PIDt94ySjKEHKKvWrYijsZtclxU'
        mdfile = get_local_path('..', 'stratuslab', market_id + '.json')
        self.assertTrue(glancing.main(['-d', mdfile]))
        self.assertTrue(glancing.main(['-d', market_id]))

class GlancingUrlDryRunTest(unittest.TestCase):

    def test_glancing_url_notenough_param(self):
        with devnull('stderr'):
            with self.assertRaises(SystemExit):
                url = 'http://nulle.part.fr/nonexistent_file.txt'
                glancing.main(['-d', url, '-s'])

    def test_glancing_url_notexistent(self):
        url = 'http://nulle.part.fr/nonexistent_file.txt'
        self.assertFalse(glancing.main(['-d', url]))

class BaseGlancingUrl(unittest.TestCase):

    _CIRROS_URL = 'http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-i386-disk.img'
    _CIRROS_SUM = 'http://download.cirros-cloud.net/0.3.4/MD5SUMS'
    _CIRROS_MD5 = '79b4436412283bb63c2cba4ac796bcd9'

class GlancingUrlDryRunCirrosTest(BaseGlancingUrl):

    def test_glancing_url(self):
        self.assertTrue(glancing.main(['-d', self._CIRROS_URL]))

    def test_glancing_url_md5(self):
        self.assertTrue(glancing.main(['-d', self._CIRROS_URL,
                                       '-s', self._CIRROS_MD5]))
        self.assertTrue(glancing.main(['-d', self._CIRROS_URL,
                                       '-S', self._CIRROS_SUM]))

@unittest.skipUnless(_GLANCE_OK, "glance not properly configured")
class GlancingUrlImportTest(BaseGlancingUrl):

    def test_glancing_url_import_no_name(self):
        name, _ = os.path.splitext(os.path.basename(self._CIRROS_URL))
        with cleanup(glance.glance_delete, name):
            self.assertTrue(glancing.main([self._CIRROS_URL]))

    @glance_cleanup()
    def test_glancing_url_import_bad_md5(self):
        self.assertFalse(glancing.main(['-n', test_name(),
            self._CIRROS_URL, '-s', '0' * 32]))

    @glance_cleanup()
    def test_glancing_url_import_bad_md5_but_force(self):
        self.assertTrue(glancing.main(['-f', '-n', test_name(),
            self._CIRROS_URL, '-s', '0' * 32]))

    @glance_cleanup()
    def test_glancing_url_import_no_md5(self):
        self.assertTrue(glancing.main(['-n', test_name(),
            self._CIRROS_URL]))

    @glance_cleanup()
    def test_glancing_url_import_good_md5(self):
        self.assertTrue(glancing.main(['-n', test_name(),
            self._CIRROS_URL, '-s', self._CIRROS_MD5]))

    @glance_cleanup()
    def test_glancing_url_import_good_sum(self):
        self.assertTrue(glancing.main(['-n', test_name(),
            self._CIRROS_URL, '-S', self._CIRROS_SUM]))

class GlancingAddChecksumTest(BaseGlancingUrl):

    def setUp(self):
        self._v = utils.get_verbose()
        utils.set_verbose(True)

    def tearDown(self):
        utils.set_verbose(self._v)

    def test_glancing_add_checksum(self):
        with utils.stringio() as output:
            with utils.redirect('stdout', output):
                self.assertFalse(glancing.add_checksum(self._CIRROS_MD5,
                                 {'checksums': {'md5': '0' * 32}}))
                self.assertEqual(output.getvalue(), '%s: conflicting digests: %s:%s\n' %
                                 (sys.argv[0], self._CIRROS_MD5, '0' * 32))
