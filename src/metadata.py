#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright © 2016 Vincent Legoll <vincent.legoll@gmail.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function

import os
import json
import hashlib
import xml.etree.ElementTree as et

import decompressor

from utils import vprint

class StratusLabNS(object):

    _NS_TO_URL_PREFIXES = {
        'dcterms': "http://purl.org/dc/terms/",
        'rdf': "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        'slreq': "http://mp.stratuslab.eu/slreq#",
        'slterms': "http://mp.stratuslab.eu/slterms#",
        'base': "http://mp.stratuslab.eu/",
    }

    _RETKEY_TO_NS_PREFIXES = {
        'os': 'slterms',
        'bytes': 'slreq',
        'title': 'dcterms',
        'format': 'dcterms',
        'version': 'slterms',
        'os-arch': 'slterms',
        'location': 'slterms',
        'algorithm': 'slreq',
        'os-version': 'slterms',
        'compression': 'dcterms',
    }

class MetaDataBase(object):

    def __init__(self):
        super(MetaDataBase, self).__init__()
        self.data = None

    def get_name(self):
        data = self.data
        return '%s-%s-%s' % (data['os'], data['os-version'], data['os-arch'])

# Translate Stratuslab market place hash names to hashlib ones
def sl_to_hashlib(hash_name):
    return hash_name.replace('-', '').lower()

class MetaDataJson(MetaDataBase):

    def __init__(self, filename):
        super(MetaDataJson, self).__init__()
        with open(filename, 'rb') as fileobj:
            try:
                self.json_obj = json.loads(fileobj.read())
            except ValueError:
                self.json_obj = None
            if not isinstance(self.json_obj, dict):
                raise ValueError('Cannnot load json data from: ' + filename)
        self.data = {'checksums': {}}

class MetaStratusLabJson(MetaDataJson):
    '''Parse the metadata .json file, from the stratuslab marketplace
       Extract interesting data: url and message digests
    '''

    _MDKEY_TO_RETKEY = {
        StratusLabNS._NS_TO_URL_PREFIXES[ns] + key: key
        for key, ns in StratusLabNS._RETKEY_TO_NS_PREFIXES.items()
    }

    def get_metadata(self):
        ret = self.data
        # StratusLab marketplace can answer with 200/OK but error encoded
        # in json response...
        if "rMsg" in self.json_obj:
            vprint('Bad JSON metadata')
            return None
        for val in self.json_obj.values():
            for key in val:
                retkey = self._MDKEY_TO_RETKEY.get(key)
                value = val[key][0]['value']
                if retkey:
                    if retkey != 'algorithm':
                        ret[retkey] = value
                    else:
                        ret['checksums'][sl_to_hashlib(value)] = (
                            val['http://mp.stratuslab.eu/slreq#value']
                            [0]['value'])
        return ret

class MetaCern(MetaDataJson):

    _RETKEY_TO_CERN = {
        'bytes': "hv:size",
        'location': "hv:uri",
        'os': "sl:os",
        'os-arch': "sl:arch",
        'os-version': "sl:osversion",
    }

    def __init__(self, jsonfile, ident):
        super(MetaCern, self).__init__(jsonfile)
        self.all_images = {}
        self.get_all_images()
        self.data = None
        self.ident = ident

    def get_metadata(self):
        return self.all_images.get(self.ident, {})

    def get_all_images(self):
        imglist = self.json_obj["hv:imagelist"]["hv:images"]
        for img_h in imglist:
            img = img_h["hv:image"]
            ret = {
                'checksums': {},
                'format': 'raw',
                'compression': None,
            }
            ext = os.path.splitext(img["hv:uri"])[1]
            if ext in decompressor._EXT_MAP:
                ret['compression'] = ext.strip('.')
            for (key, val) in self._RETKEY_TO_CERN.iteritems():
                ret[key] = img[val]
            for algo in hashlib.algorithms:
                key = "sl:checksum:" + algo
                if key in img:
                    ret['checksums'][algo] = img[key]
            self.all_images[img["dc:identifier"]] = ret

class MetaStratusLabXml(MetaDataBase):
    '''Parse the metadata .xml file, from the stratuslab marketplace
       Extract interesting data: url and message digests
    '''

    def __init__(self, filename):
        super(MetaStratusLabXml, self).__init__()
        try:
            self.xml_obj = et.parse(filename)
        except et.ParseError:
            vprint('XML parse error')
            self.xml_obj = None
        except:
            vprint('Parsed OK, but still no XML object from:' + str(filename))
        self.data = {'checksums': {}}

    def get_metadata(self):
        if not self.xml_obj:
            vprint('No XML object')
            return None
        nsp = StratusLabNS._NS_TO_URL_PREFIXES
        ret = self.data
        root = self.xml_obj.getroot()
        # StratusLab xml metadata files are not consistent:
        # if downloaded through the website XML button or directly
        # through the url, there's an additionnal "<metadata>" root tag
        # SL_URI_BASE: https://marketplace.stratuslab.eu/marketplace/metadata
        # Manually crafted URI
        # <SL_URI_BASE>/LHfKVPoHcv4oMirHU0KuOQc-TvI?media=xml
        # Button URI:
        # <SL_URI_BASE>/LHfKVPoHcv4oMirHU0KuOQc-TvI/<ENDORSER>/<DATE>?media=xml
        if root.tag == 'metadata':
            rdf = root.find('rdf:RDF', nsp)
        else:
            rdf = root
        desc = rdf.find('rdf:Description', nsp)
        for cksum in desc.findall('slreq:checksum', nsp):
            algo = cksum.find('slreq:algorithm', nsp)
            val = cksum.find('slreq:value', nsp)
            ret['checksums'][sl_to_hashlib(algo.text)] = val.text
        for key, val in StratusLabNS._RETKEY_TO_NS_PREFIXES.items():
            if key == 'algorithm':
                continue
            mdkey = val + ':' + key
            node = desc.find(mdkey, nsp)
            if node is not None:
                ret[key] = node.text
        return ret
