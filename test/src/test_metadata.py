#! /usr/bin/env python

import os
import unittest

from tutils import local_pythonpath, get_local_path

# Setup project-local PYTHONPATH
local_pythonpath('..', '..', 'src')

from utils import devnull

import metadata

good_keys_cern = set([
    'os',
    'bytes',
    'format',
    'os-arch',
    'location',
    'checksums',
    'os-version',
    'compression',
])

good_keys_sl = good_keys_cern | set(['title', 'version'])

class MetaDataStratusLabJsonTest(unittest.TestCase):

    def test_metadata_json(self):
        fn = 'PIDt94ySjKEHKKvWrYijsZtclxU.json'
        jsonfile = get_local_path('..', 'stratuslab', fn)
        m = metadata.MetaStratusLabJson(jsonfile)
        md = m.get_metadata()
        self.assertEqual(set(md.keys()), good_keys_sl)
        self.assertEqual(md['location'],
                         'http://appliances.stratuslab.eu/images/base/CentOS-'
                         '7-Server-x86_64/1.1/CentOS-7-Server-x86_64.dsk.gz')

    def test_metadata_json_no_md_matching_query(self):
        fn = 'LHfKVPoHcv4oMirHU0KuOQc-TvI?media=json'
        jsonfile = get_local_path('..', 'stratuslab', fn)
        m = metadata.MetaStratusLabJson(jsonfile)
        md = m.get_metadata()
        self.assertIsNone(md)

    def test_metadata_json_bad(self):
        with devnull('stderr'):
            with self.assertRaises(ValueError):
                metadata.MetaStratusLabJson(os.devnull)

class MetaDataCernTest(unittest.TestCase):

    def test_metadata_cern(self):
        fn = 'test_image_list'
        jsonfile = get_local_path('..', 'CERN', fn)
        m = metadata.MetaCern(jsonfile, 'deadbabe-f00d-beef-cafe-b1ab1ab1a666')
        md = m.get_metadata()
        self.assertEqual(set(md.keys()), good_keys_cern)
        self.assertEqual(md['location'],
                         'http://download.cirros-cloud.net/0.3.4/'
                         'cirros-0.3.4-i386-disk.img')

class MetaDataStratusLabXmlTest(unittest.TestCase):

    def test_metadata_xml(self):
        fn = 'Buh-tYElvOEvst1HDyTq_6v-1si.xml'
        xmlfile = get_local_path('..', 'stratuslab', fn)
        self.assertTrue(os.path.exists(xmlfile))
        m = metadata.MetaStratusLabXml(xmlfile)
        self.assertTrue(m is not None)
        md = m.get_metadata()
        self.assertTrue(md is not None)
        self.assertEqual(set(md.keys()), good_keys_sl)
        self.assertEqual(md['location'],
                         'http://grand-est.fr/resources/CLOUD/'
                         'precise-server-cloudimg-amd64-disk1.img')
        self.assertEqual(m.get_name(), 'Ubuntu-12.04-x86_64')

    def test_metadata_xml_button_vs_wget(self):
        fn_base = 'LHfKVPoHcv4oMirHU0KuOQc-TvI.%s.xml'
        fn = fn_base % 'button'
        xmlfile = get_local_path('..', 'stratuslab', fn)
        m = metadata.MetaStratusLabXml(xmlfile)
        md = m.get_metadata()
        self.assertEqual(set(md.keys()), good_keys_sl)

        fn = fn_base % 'wget'
        xmlfile = get_local_path('..', 'stratuslab', fn)
        m = metadata.MetaStratusLabXml(xmlfile)
        md = m.get_metadata()
        self.assertEqual(set(md.keys()), good_keys_sl)

    def test_metadata_xml_bad(self):
        m = metadata.MetaStratusLabXml(os.devnull)
        self.assertIsNone(m.get_metadata())

class MetaDataJsonFixtureTest(unittest.TestCase):

    fn = 'test.json'

    def setUp(self):
        if os.path.exists(self.fn):
            os.remove(self.fn)

    tearDown = setUp

    def test_metadata_json_fixture_not_dict(self):
        with open(self.fn, 'wb') as jsonf:
            jsonf.write('""\n')
        with devnull('stderr'):
            with self.assertRaises(ValueError):
                metadata.MetaStratusLabJson(self.fn)
