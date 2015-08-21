#! /usr/bin/env python

import os
import sys
import unittest

from tutils import get_local_path

# Setup PYTHONPATH for glancing
sys.path.append(get_local_path('..', '..', 'src'))

from utils import devnull, environ, test_name, run, cleanup

import glancing

# Check we have a cloud ready to import images into...
_GLANCE_OK = False
with devnull('stderr'):
    _GLANCE_OK = run(['glance', 'image-list'])[0]

# Avoid heavy image download tests
_HEAVY_TESTS = False
_HUGE_TESTS = False # 5 GB image

class TestGlancingMisc(unittest.TestCase):

    def glancing_test_main_glance_availability(self):
        with environ('PATH'):
            self.assertFalse(glancing.main(['image', os.devnull]))

class TestGlancingImage(unittest.TestCase):

    _TTYLINUX_FILE = get_local_path('..', 'images', 'ttylinux-16.1-x86_64.img')
    _TTYLINUX_MD5 = '3d1b4804dcf2a613f0ed4a91b9ed2b98'
    _DEVNULL_MD5 = 'd41d8cd98f00b204e9800998ecf8427e'

    def glancing_test_image_no_param(self):
        with devnull('stderr'):
            with self.assertRaises(SystemExit):
                glancing.main(['-d', 'image'])

    def glancing_test_image_notenough_param(self):
        with devnull('stderr'):
            with self.assertRaises(SystemExit):
                glancing.main(['-d', 'image', os.devnull, '-s'])

    def glancing_test_image_devnull_bad_sum(self):
        self.assertFalse(glancing.main(['-d', 'image', os.devnull, '-s', '### BAD CHECKSUM ###']))

    def glancing_test_image_devnull_null_sum(self):
        self.assertFalse(glancing.main(['-d', 'image', os.devnull, '-s', '0' * 32]))

    def glancing_test_image_devnull(self):
        self.assertTrue(glancing.main(['-d', 'image', os.devnull, '-s', self._DEVNULL_MD5]))

    def glancing_test_image_devnull_verbose(self):
        self.assertTrue(glancing.main(['-dv', 'image', os.devnull, '-s', self._DEVNULL_MD5]))

    def glancing_test_image_devnull_conflicting_digests(self):
        self.assertFalse(glancing.main(['-d', 'image', os.devnull, '-s', self._DEVNULL_MD5 + ':' + '0' * 32]))

    def glancing_test_image_notexistent(self):
        self.assertFalse(glancing.main(['-d', 'image', '/notexistent.txt']))

    def glancing_test_image_notexistent_sum(self):
        self.assertFalse(glancing.main(['-d', 'image', '/notexistent.txt', '-s', self._DEVNULL_MD5]))

    def glancing_test_image_one(self):

        md5 = self._TTYLINUX_MD5
        sha1 = '1b5229d5dad92bc7952553be01608af2180eafbe'
        sha512 = '79556bc3a25e4555a6cd71afba8eae80eb6d5f23f16a84e6017a54469034cf77ee7bcd74ac285c6ec42c25547b6963c1e7232d4fcca388a326f0ec3e7afb838e'

        self.assertTrue(glancing.main(['-d', 'image', self._TTYLINUX_FILE]))
        self.assertTrue(glancing.main(['-d', 'image', self._TTYLINUX_FILE, '-s', '']))
        self.assertTrue(glancing.main(['-d', 'image', self._TTYLINUX_FILE, '-s', ':']))
        self.assertTrue(glancing.main(['-d', 'image', self._TTYLINUX_FILE, '-s', ':::::']))
        self.assertTrue(glancing.main(['-d', 'image', self._TTYLINUX_FILE, '-s', sha512]))
        self.assertTrue(glancing.main(['-d', 'image', self._TTYLINUX_FILE, '-s', sha1 + ':' + md5]))
        self.assertTrue(glancing.main(['-d', 'image', self._TTYLINUX_FILE, '-s', md5 + ':']))
        self.assertTrue(glancing.main(['-d', 'image', self._TTYLINUX_FILE, '-s', ':' + md5]))
        self.assertFalse(glancing.main(['-d', 'image', self._TTYLINUX_FILE, '-s', 'a' + md5]))
        self.assertFalse(glancing.main(['-d', 'image', self._TTYLINUX_FILE, '-s', 'a' + md5 + ':' + md5]))
        self.assertFalse(glancing.main(['-d', 'image', self._TTYLINUX_FILE, '-s', md5[:12] + '0' + md5[13:]]))
        self.assertFalse(glancing.main(['-d', 'image', self._TTYLINUX_FILE, '-s', md5 + ':' + md5[:12] + '0' + md5[13:]]))

    def glancing_test_image_two(self):
        fn = 'coreos_production_qemu_image.img'
        imgfile = get_local_path('..', 'images', fn)
        md5 = '1b0d8f7e4ff1128e3527ad6e15ae0855'
        self.assertTrue(glancing.main(['-d', 'image', imgfile, '-s', md5 + ':' + md5]))

    @unittest.skipUnless(_GLANCE_OK, "glance not properly configured")
    def glancing_test_image_import_noname(self):
        name, ext = os.path.splitext(os.path.basename(self._TTYLINUX_FILE))
        with cleanup(['glance', 'image-delete', name]):
            self.assertTrue(glancing.main(['-f', 'image', self._TTYLINUX_FILE,
                                           '-s', self._TTYLINUX_MD5]))

    @unittest.skipUnless(_GLANCE_OK, "glance not properly configured")
    def glancing_test_image_import_name(self):
        with cleanup(['glance', 'image-delete', test_name()]):
            self.assertTrue(glancing.main(['-n', test_name(), 'image',
                                          self._TTYLINUX_FILE, '-s', self._TTYLINUX_MD5]))

    @unittest.skipUnless(_GLANCE_OK, "glance not properly configured")
    def glancing_test_image_import_name_bad_md5(self):
        with cleanup(['glance', 'image-delete', test_name()]):
            self.assertFalse(glancing.main(['-n', test_name(), 'image',
                                           self._TTYLINUX_FILE, '-s', '0' * 32]))

    @unittest.skipUnless(_GLANCE_OK, "glance not properly configured")
    def glancing_test_image_import_name_force(self):
        with cleanup(['glance', 'image-delete', test_name()]):
            self.assertTrue(glancing.main(['-f', '-n', test_name(), 'image',
                                          self._TTYLINUX_FILE, '-s', '0' * 32]))

class TestGlancingMetadata(unittest.TestCase):

    def glancing_test_metadata_cli_params(self):
        with devnull('stderr'):
            with self.assertRaises(SystemExit):
                glancing.main(['-d', 'json'])
            with self.assertRaises(SystemExit):
                glancing.main(['-d', 'market'])
            with self.assertRaises(IOError):
                self.assertFalse(glancing.main(['-d', 'json', '']))
            self.assertFalse(glancing.main(['-d', 'market', '']))

    def glancing_test_metadata_cli_bad_format(self):
        with devnull('stderr'):
            with self.assertRaises(ValueError):
                glancing.main(['-d', 'json', os.devnull])
            self.assertFalse(glancing.main(['-d', 'market', os.devnull]))

    @unittest.skipUnless(_HEAVY_TESTS, "image too big")
    def glancing_test_metadata_heavies(self):
        market_ids = (
            ('JcqGhHxmTRAEpHMmRF-xhSTM3TO', False, False), # 98 MB, size & checksum mismatch: 4 B -> 98 MB
            ('BtSKdXa2SvHlSVTvgFgivIYDq--', True, False), # 102 MB, does not exists any more on SL marketplace
            ('KqU_1EZFVGCDEhX9Kos9ckOaNjB', True, True), # 463 MB
            ('ME4iRTemHRwhABKV5AgrkQfDerA', False, False), # Size & checksum mismatch: 375 MB -> 492 MB
        )
        for market_id, status_json, status_market in market_ids:
            mdfile = get_local_path('..', 'stratuslab', market_id + '.json')
            self.assertEqual(status_json, glancing.main(['-d', 'json', mdfile]), mdfile)
            self.assertEqual(status_market, glancing.main(['-d', 'market', market_id]), market_id)

    @unittest.skipUnless(_HEAVY_TESTS, "image too big")
    @unittest.skipUnless(_GLANCE_OK, "glance not properly configured")
    def glancing_test_metadata_bad_but_force(self):
        # Size & checksum mismatch: 375 MB -> 492 MB
        market_id = 'ME4iRTemHRwhABKV5AgrkQfDerA'
        mdfile = get_local_path('..', 'stratuslab', market_id + '.json')
        with cleanup(['glance', 'image-delete', test_name()]):
            self.assertTrue(glancing.main(['-f', '-n', test_name(), 'json', mdfile]))
        with cleanup(['glance', 'image-delete', test_name()]):
            self.assertTrue(glancing.main(['-f', '-n', test_name(), 'market', market_id]))

    @unittest.skipUnless(_GLANCE_OK, "glance not properly configured")
    def glancing_test_metadata_cirros_import(self):
        # 12 MB
        mdfile = get_local_path('..', 'stratuslab', 'cirros.json')
        with devnull('stderr'):
            with cleanup(['glance', 'image-delete', test_name()]):
                self.assertTrue(glancing.main(['-v', '-n', test_name(), 'json', mdfile, '-k']))

    @unittest.skipUnless(_GLANCE_OK, "glance not properly configured")
    def glancing_test_metadata_cirros_import_bad_size_force(self):
        # 12 MB
        mdfile = get_local_path('..', 'stratuslab', 'cirros_bad_size.json')
        with devnull('stderr'):
            with cleanup(['glance', 'image-delete', test_name()]):
                self.assertTrue(glancing.main(['-f', '-n', test_name(), 'json', mdfile]))

    @unittest.skipUnless(_GLANCE_OK, "glance not properly configured")
    def glancing_test_metadata_cirros_import_bad_size(self):
        # 12 MB
        mdfile = get_local_path('..', 'stratuslab', 'cirros_bad_size.json')
        with devnull('stderr'):
            with cleanup(['glance', 'image-delete', test_name()]):
                self.assertFalse(glancing.main(['-n', test_name(), 'json', mdfile]))

    @unittest.skipUnless(_HUGE_TESTS, "image too big: 5.0 GB")
    def glancing_test_metadata_big(self):
        market_id = 'PIDt94ySjKEHKKvWrYijsZtclxU'
        mdfile = get_local_path('..', 'stratuslab', market_id + '.json')
        self.assertFalse(glancing.main(['-d', 'json', mdfile]))
        self.assertFalse(glancing.main(['-d', 'market', market_id]))

class BaseGlancingUrl(unittest.TestCase):

    _CIRROS_URL = 'http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-i386-disk.img'
    _CIRROS_MD5 = '79b4436412283bb63c2cba4ac796bcd9'

class TestGlancingUrlDryRun(BaseGlancingUrl):

    def glancing_test_url_no_param(self):
        with devnull('stderr'):
            with self.assertRaises(SystemExit):
                glancing.main(['-d', 'url'])

    def glancing_test_url_notenough_param(self):
        with devnull('stderr'):
            with self.assertRaises(SystemExit):
                url = 'http://nulle.part.fr/nonexistent_file.txt'
                glancing.main(['-d', 'url', url, '-s'])

    def glancing_test_url_notexistent(self):
        url = 'http://nulle.part.fr/nonexistent_file.txt'
        self.assertFalse(glancing.main(['-d', 'url', url]))

    def glancing_test_url(self):
        self.assertTrue(glancing.main(['-d', 'url', self._CIRROS_URL]))

@unittest.skipUnless(_GLANCE_OK, "glance not properly configured")
class TestGlancingUrlImport(BaseGlancingUrl):

    def glancing_test_url_import_no_name(self):
        name, ext = os.path.splitext(os.path.basename(self._CIRROS_URL))
        with cleanup(['glance', 'image-delete', name]):
            self.assertTrue(glancing.main(['url', self._CIRROS_URL]))

    def glancing_test_url_import_bad_md5(self):
        with cleanup(['glance', 'image-delete', test_name()]):
            self.assertFalse(glancing.main(['-n', test_name(), 'url', self._CIRROS_URL, '-s', '0' * 32]))

    def glancing_test_url_import_bad_md5_but_force(self):
        with cleanup(['glance', 'image-delete', test_name()]):
            self.assertTrue(glancing.main(['-f', '-n', test_name(), 'url', self._CIRROS_URL, '-s', '0' * 32]))

    def glancing_test_url_import_no_md5(self):
        with cleanup(['glance', 'image-delete', test_name()]):
            self.assertTrue(glancing.main(['-n', test_name(), 'url', self._CIRROS_URL]))

    def glancing_test_url_import_good_md5(self):
        with cleanup(['glance', 'image-delete', test_name()]):
            self.assertTrue(glancing.main(['-n', test_name(), 'url', self._CIRROS_URL, '-s', self._CIRROS_MD5]))
