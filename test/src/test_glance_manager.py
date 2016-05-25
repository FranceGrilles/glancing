#! /usr/bin/env python

import os
import sys
import unittest

from tutils import local_pythonpath, get_local_path

# Setup project-local PYTHONPATH
local_pythonpath('..', '..', 'src')

import utils
import glance_manager

utils.set_verbose(True)

# Check we have a cloud ready to import images into...
_GLANCE_OK = False
with utils.devnull('stderr'):
    _GLANCE_OK = utils.run(['glance', 'image-list'])[0]

_OLDGMF = glance_manager.get_meta_file

@unittest.skipUnless(_GLANCE_OK, "glance not properly configured")
class GlanceManagerTest(unittest.TestCase):

    def setUp(self):
        gmf = lambda mpid, url: get_local_path('..', 'stratuslab', 'cirros.xml')
        glance_manager.get_meta_file = gmf

    def tearDown(self):
        glance_manager.get_meta_file = _OLDGMF

    def test_glance_manager_mocked_ok(self):
        with utils.cleanup(['glance', '--os-image-api-version', '1', 'image-delete', 'GLANCE_MANAGER_CIRROS_TESTING_IMAGE']):
            self.assertTrue(glance_manager.main(['-v', '-l',
                get_local_path('..', 'gm_list.txt')]))

# TODO: test name with spaces characters (initial, update, etc...)
