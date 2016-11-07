#! /usr/bin/env python

import os
import unittest

from tutils import local_pythonpath, get_local_path

# Setup project-local PYTHONPATH
local_pythonpath('..', '..', 'src')

import glance
import utils
import openstack_out

# Always verbose messages during tests
utils.set_verbose(True)

# Check we have a cloud ready to import images into...
_GLANCE_OK = False
with utils.devnull('stderr'):
    _GLANCE_OK = utils.run(['glance', 'image-list'])[0]

@unittest.skipUnless(_GLANCE_OK, "glance not properly configured")
class SkipGlanceNOK(unittest.TestCase):
    pass

class GlanceTest(SkipGlanceNOK):

    def test_glance_ok(self):
        self.assertTrue(glance.glance_ok())
        with utils.devnull('stderr'):
            with utils.environ('PATH', 'not_the_one'):
                self.assertFalse(glance.glance_ok())

    def test_glance_exists_raise(self):
        with self.assertRaises(TypeError):
            glance.glance_exists(None)
        with self.assertRaises(TypeError):
            glance.glance_exists(True)
        with self.assertRaises(TypeError):
            glance.glance_exists(False)
        with self.assertRaises(TypeError):
            glance.glance_exists([])

    def test_glance_exists_false(self):
        self.assertFalse(glance.glance_exists(''))
        self.assertFalse(glance.glance_exists('Nonexistent'))
        self.assertFalse(glance.glance_exists(u''))
        self.assertFalse(glance.glance_exists(u'Nonexistent'))

    def test_glance_show_nok(self):
        self.assertFalse(glance.glance_show(''))
        self.assertFalse(glance.glance_show('Nonexistent'))
        self.assertFalse(glance.glance_show(u''))
        self.assertFalse(glance.glance_show(u'Nonexistent'))

    def test_glance_import_id_ok(self):
        vmid = glance.glance_import_id(os.devnull, name=None)
        self.assertFalse(vmid)
        vmid = glance.glance_import_id(os.devnull, name=None, diskformat='raw')
        self.assertTrue(vmid)
        self.assertTrue(glance.glance_delete_ids([vmid]))

    def test_glance_import_id_nok(self):
        self.assertFalse(glance.glance_import_id(os.devnull, md5='0', name='devnull'))

class GlanceIdsTest(SkipGlanceNOK):

    def test_glance_ids_unfiltered(self):
        l1 = glance.glance_ids(None)
        self.assertTrue(set() <= l1)
        l2 = glance.glance_ids()
        self.assertTrue(set() <= l2)
        self.assertEqual(l1, l2)

    def test_glance_ids_single(self):
        self.assertEqual(set(), glance.glance_ids(True))
        self.assertEqual(set(), glance.glance_ids(False))
        self.assertEqual(set(), glance.glance_ids(''))
        self.assertEqual(set(), glance.glance_ids(u''))
        self.assertEqual(set(), glance.glance_ids([]))

    def test_glance_ids_list_single(self):
        self.assertEqual(set(), glance.glance_ids([None]))
        self.assertEqual(set(), glance.glance_ids([True]))
        self.assertEqual(set(), glance.glance_ids([False]))
        self.assertEqual(set(), glance.glance_ids(['']))
        self.assertEqual(set(), glance.glance_ids([u'']))
        self.assertEqual(set(), glance.glance_ids([[]]))

    def test_glance_ids_list(self):
        self.assertEqual(set(), glance.glance_ids([None, True, False]))
        self.assertEqual(set(), glance.glance_ids(['', u'']))

    def test_glance_ids_tenant(self):
        add_args = []
        if 'OS_TENANT_ID' in os.environ:
            add_args = ['--owner', os.environ['OS_TENANT_ID']]
        elif 'OS_TENANT_NAME' in os.environ:
            ret = utils.run(['keystone', 'tenant-get',
                             os.environ['OS_TENANT_NAME']], out=True, err=True)
            status, _, out, err = ret
            if status:
                self.assertTrue(len(out) > 0)
                _, block, _, _ = openstack_out.parse_block(out)
                self.assertTrue(len(block) > 0)
                for prop, val in block:
                    if prop == 'id':
                        add_args = ['--owner', val]
                        break
                self.assertTrue(False, 'TENANT not found by keystone...')
            else:
                print 'OUT:', out
                print 'ERR:', err
                self.assertTrue(False)
        self.assertTrue(len(add_args) == 2)
        l1 = glance.glance_ids(None, *add_args)
        self.assertTrue(set() < l1)
        # We can see more images if we are administrator and don't filter on tenant
        l2 = glance.glance_ids(names=None)
        self.assertTrue(set() < l1 <= l2)

class TestGlanceNotOkGlanceIDS(SkipGlanceNOK):

    def test_glance_ids_uuid(self):
        glance.glance_delete_all(utils.test_name(), quiet=True)
        ret = glance.glance_import(os.devnull, name=utils.test_name(),
                                   diskformat='raw')
        self.assertTrue(ret)
        img_uuids_name = list(glance.glance_ids(utils.test_name()))
        self.assertEqual(len(img_uuids_name), 1)
        img_uuid = img_uuids_name[0]
        img_uuids_uuid = list(glance.glance_ids(img_uuid))
        self.assertEqual(img_uuids_uuid, img_uuids_name)
        glance.glance_delete_all(utils.test_name(), quiet=True)

class TestGlanceNotOk(SkipGlanceNOK):

    def test_glance_diskformat(self):
        glance.glance_delete_all(utils.test_name(), quiet=True)
        ret = glance.glance_import(os.devnull, name=utils.test_name(),
                                   diskformat='notgood')
        self.assertFalse(ret)
        ret = glance.glance_import(os.devnull, name=utils.test_name())
        self.assertFalse(ret)
        glance.glance_delete_all(utils.test_name(), quiet=True)

    def test_glance_imglist(self):
        self.assertTrue(glance.glance_run('image-list'))
        with utils.environ('OS_PASSWORD', 'not_the_one'):
            self.assertFalse(glance.glance_run('image-list'))

    def test_glance_ids(self):
        self.assertEqual(set(), glance.glance_ids('XXX'))
        with utils.environ('OS_PASSWORD', 'not_the_one'):
            self.assertEqual(set(), glance.glance_ids('XXX'))

class TestGlanceFixture(SkipGlanceNOK):

    _IMG_NAME = 'test-glance-img'
    _IMG_ID = None

    def setUp(self):
        if self._IMG_ID:
            glance.glance_delete_all(self._IMG_ID, quiet=True)
        if self._IMG_NAME:
            glance.glance_delete_all(self._IMG_NAME, quiet=True)

    tearDown = setUp

    def common_start(self, filename=os.devnull):
        self.assertFalse(glance.glance_exists(self._IMG_NAME))
        self._IMG_ID = glance.glance_import_id(filename, name=self._IMG_NAME, diskformat='raw')
        # Be extra careful, to avoid calling glance_delete_all with wrong parameters
        self.assertTrue(self._IMG_ID is not None)
        self.assertTrue(self._IMG_ID is not False)
        self.assertTrue(len(self._IMG_ID) > 0)
        self.assertTrue(self._IMG_ID)
        self.assertTrue(glance.glance_exists(self._IMG_ID))
        self.assertTrue(glance.glance_exists(self._IMG_NAME))

class GlanceNoNameTest(TestGlanceFixture):

    # An empty name should be OK
    _IMG_NAME = ''

    def test_glance_main_emptyname_delete_byname(self):
        self.common_start()
        self.assertTrue(self._IMG_ID is not None)
        self.assertTrue(len(self._IMG_ID) > 0)
        self.assertTrue(glance.main(['-v', '-d', self._IMG_NAME]))
        self.assertFalse(glance.glance_exists(self._IMG_ID))
        self.assertFalse(glance.glance_exists(self._IMG_NAME))

    def test_glance_main_emptyname_delete_byid(self):
        self.common_start()
        self.assertTrue(self._IMG_ID is not None)
        self.assertTrue(len(self._IMG_ID) > 0)
        self.assertTrue(glance.main(['-v', '-d', self._IMG_ID]))
        self.assertFalse(glance.glance_exists(self._IMG_ID))
        self.assertFalse(glance.glance_exists(self._IMG_NAME))

class GlanceNoNameTestUnicode(GlanceNoNameTest):

    # An empty unicode name should be OK
    _IMG_NAME = u''

class GlanceMainTest(TestGlanceFixture):

    def test_glance_main_ok_nodelete(self):
        self.common_start()
        self.assertTrue(glance.main(['-v']))
        self.assertTrue(glance.glance_exists(self._IMG_NAME))

    def test_glance_main_ok(self):
        self.common_start()
        self.assertTrue(glance.main(['-d', self._IMG_NAME]))
        self.assertFalse(glance.glance_exists(self._IMG_NAME))

    def test_glance_main_ok_verbose(self):
        self.common_start()
        self.assertTrue(glance.main(['-v', '-d', self._IMG_NAME]))
        self.assertFalse(glance.glance_exists(self._IMG_NAME))

    def test_glance_main_fail_wrong_param_delete(self):
        self.common_start()
        with self.assertRaises(SystemExit):
            with utils.devnull('stderr'):
                glance.main(['-d'])
        self.assertTrue(glance.glance_exists(self._IMG_NAME))

    def test_glance_main_fail_listing_ids(self):
        with utils.environ('OS_PASSWORD', ''):
            self.assertFalse(glance.main([]))

    def test_glance_main_fail_wrong_param_name(self):
        self.common_start()
        with self.assertRaises(SystemExit):
            with utils.devnull('stderr'):
                glance.main([self._IMG_NAME])
        self.assertTrue(glance.glance_exists(self._IMG_NAME))

class GlanceDeleteTest(TestGlanceFixture):

    def test_glance_delete_all(self):
        self.common_start()
        self.assertTrue(glance.glance_import(os.devnull, name=self._IMG_NAME, diskformat='raw'))
        self.assertTrue(glance.glance_import(os.devnull, name=self._IMG_NAME, diskformat='raw'))
        self.assertTrue(glance.glance_exists(self._IMG_NAME))
        self.assertTrue(glance.glance_delete_all(self._IMG_NAME))
        self.assertFalse(glance.glance_exists(self._IMG_NAME))

    def test_glance_delete_all_fail(self):
        self.common_start()
        self.assertTrue(glance.glance_import(os.devnull, name=self._IMG_NAME, diskformat='raw'))
        self.assertTrue(glance.glance_import(os.devnull, name=self._IMG_NAME, diskformat='raw'))
        self.assertTrue(glance.glance_exists(self._IMG_NAME))
        self.assertFalse(glance.glance_exists(self._IMG_NAME + '-nothere'))
        self.assertTrue(glance.glance_delete_all([self._IMG_NAME, self._IMG_NAME + '-nothere']))
        self.assertFalse(glance.glance_exists(self._IMG_NAME))
        self.assertFalse(glance.glance_exists(self._IMG_NAME + '-nothere'))

    def test_glance_delete_ok(self):
        self.common_start()
        self.assertTrue(glance.glance_delete(self._IMG_NAME))
        self.assertFalse(glance.glance_exists(self._IMG_NAME))

    def test_glance_delete_ids_empty(self):
        self.assertTrue(glance.glance_delete_ids([]))
        self.assertFalse(glance.glance_delete_ids(['']))
        self.assertFalse(glance.glance_delete_ids(['', '']))

    def test_glance_delete_ids_combined_before(self):
        self.common_start()
        self.assertFalse(glance.glance_delete_ids([self._IMG_ID, '']))

    def test_glance_delete_ids_combined_after(self):
        self.common_start()
        self.assertFalse(glance.glance_delete_ids(['', self._IMG_ID]))

    def test_glance_delete_id(self):
        self.common_start()
        self.assertTrue(glance.glance_delete(self._IMG_ID))
        self.assertFalse(glance.glance_exists(self._IMG_NAME))
        self.assertFalse(glance.glance_exists(self._IMG_ID))

    def test_glance_delete_ok_quiet(self):
        self.common_start()
        self.assertTrue(glance.glance_delete(self._IMG_NAME, quiet=True))
        self.assertFalse(glance.glance_exists(self._IMG_NAME))

    def test_glance_delete_fail(self):
        self.common_start()
        self.assertTrue(glance.glance_delete(self._IMG_NAME))
        self.assertFalse(glance.glance_exists(self._IMG_NAME))

        self.assertFalse(glance.glance_delete(self._IMG_NAME))

    def test_glance_delete_fail_quiet(self):
        self.common_start()
        self.assertTrue(glance.glance_delete(self._IMG_NAME, quiet=True))
        self.assertFalse(glance.glance_exists(self._IMG_NAME))

        self.assertFalse(glance.glance_delete(self._IMG_NAME, quiet=True))

class GlanceMiscTest(TestGlanceFixture):

    def test_glance_exists_import(self):
        self.common_start()

class GlanceRenameTest(TestGlanceFixture):

    def test_glance_rename_and_back(self):
        old = '_rename_test'
        self.common_start()
        self.assertFalse(glance.glance_exists(self._IMG_NAME + old))
        self.assertTrue(glance.glance_rename(self._IMG_NAME, self._IMG_NAME + old))
        self.assertFalse(glance.glance_exists(self._IMG_NAME))
        self.assertTrue(glance.glance_exists(self._IMG_NAME + old))
        self.assertTrue(glance.glance_rename(self._IMG_NAME + old, self._IMG_NAME))
        self.assertFalse(glance.glance_exists(self._IMG_NAME + old))
        self.assertTrue(glance.glance_exists(self._IMG_NAME))

    def test_glance_rename_inexistent(self):
        old = '_rename_test'
        self.common_start()
        self.assertFalse(glance.glance_exists(self._IMG_NAME + old))
        self.assertFalse(glance.glance_exists(self._IMG_NAME + 'inexistent'))
        self.assertFalse(glance.glance_rename(self._IMG_NAME + 'inexistent', self._IMG_NAME + old))
        self.assertTrue(glance.glance_exists(self._IMG_NAME))
        self.assertFalse(glance.glance_exists(self._IMG_NAME + old))
        self.assertFalse(glance.glance_exists(self._IMG_NAME + 'inexistent'))

    def test_glance_rename_to_same_name(self):
        self.common_start()
        # This should be a NO-OP...
        self.assertTrue(glance.glance_rename(self._IMG_NAME, self._IMG_NAME))
        self.assertTrue(glance.glance_exists(self._IMG_NAME))

    def test_glance_rename_multi(self):
        # Rename multiple images with same name...
        self.common_start()
        self.assertTrue(glance.glance_exists(self._IMG_NAME))
        IMG_ID = glance.glance_import_id(os.devnull, name=self._IMG_NAME, diskformat='raw')
        self.assertTrue(IMG_ID)
        self.assertTrue(glance.glance_exists(IMG_ID))
        self.assertTrue(glance.glance_exists(self._IMG_NAME))
        self.assertTrue(len(glance.glance_ids(self._IMG_NAME)) == 2)
        self.assertTrue(glance.glance_rename(self._IMG_NAME, self._IMG_NAME + '_rename_multi'))
        # One has been renamed, the other stayed as-is...
        self.assertTrue(glance.glance_exists(self._IMG_NAME + '_rename_multi'))
        self.assertTrue(glance.glance_exists(self._IMG_NAME))
        self.assertTrue(glance.glance_exists(self._IMG_ID))
        self.assertTrue(glance.glance_exists(IMG_ID))
        # Get it back to its previous name, so that it is cleaned up
        self.assertTrue(glance.glance_rename(self._IMG_NAME + '_rename_multi', self._IMG_NAME))

class GlanceDownloadTest(TestGlanceFixture):

    def test_glance_download(self):
        _RND1M_FILE = get_local_path('..', 'data', 'random_1M.bin')
        _DL_ED_FILE = os.path.join('/', 'tmp', self._IMG_NAME)

        if os.path.exists(_DL_ED_FILE):
            os.remove(_DL_ED_FILE)

        self.common_start(_RND1M_FILE)
        self.assertTrue(glance.glance_download(self._IMG_NAME, _DL_ED_FILE))
        self.assertTrue(os.path.exists(_DL_ED_FILE))
        self.assertTrue(utils.run(['cmp', _RND1M_FILE, _DL_ED_FILE])[0])
        os.remove(_DL_ED_FILE)
        self.assertFalse(os.path.exists(_DL_ED_FILE))
        self.assertFalse(glance.glance_download('', _DL_ED_FILE))
        self.assertFalse(os.path.exists(_DL_ED_FILE))
