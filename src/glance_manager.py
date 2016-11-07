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

'''
Utility script to automatically distribute cloud images from the
France Grilles marketplace.

Manage the list of endorsed images to be distributed across all
IdGC / France-Grilles sites.
'''

import os
import sys
import argparse

import utils
import glance
import glancing
import metadata
import openstack_out

from utils import vprint

_DEFAULT_VMLIST_FILE = os.path.join('/', 'etc', 'glancing', 'vmlist')
_DEFAULT_SL_MP_URL = 'https://marketplace.stratuslab.eu/marketplace/metadata/'

def do_argparse(sys_argv):
    '''Handle CLI options
    '''
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Display additional information')

    parser.add_argument('-l', '--vmlist', default=[],
                        action='append',
                        help='File containing a list of endorsed VM image '
                             'marketplace IDs to upload in glance')

    parser.add_argument('-u', '--url', default=_DEFAULT_SL_MP_URL,
                        help='Market place base URL (default should be OK)')

    args = parser.parse_args(sys_argv)

    if args.verbose:
        utils.set_verbose(True)
        vprint('verbose mode')

    return args

def get_vmlist(vmlist):
    '''Get list of StratusLab ID of images to download

    vmlist is a list of files containing VM image marketplace IDs
    '''
    ret = set()
    for img_list_fn in vmlist:
        with open(img_list_fn, 'rb') as vmlist_f:
            for lineno, line in enumerate(vmlist_f):
                stripl = line.strip()
                # Ignore blank lines
                if not stripl:
                    continue
                # Ignore commented lines
                if stripl.startswith('#'):
                    continue
                if stripl in ret:
                    vprint('Warning @ %s:%d: ignoring duplicated image "%s".' %
                           (img_list_fn, lineno, stripl))
                    continue
                if ' ' in stripl:
                    vprint('Warning @ %s:%d: ignoring line containing '
                           'whitespace:\n%s' % (img_list_fn, lineno, stripl))
                    continue
                # Assume one valid image ID per line
                ret.add(stripl)
    return ret

_GLANCE_IMAGES = None

def get_glance_images():
    '''Get info about images already in glance
       Cache those informations to speedup subsequent calls
    '''
    global _GLANCE_IMAGES
    if _GLANCE_IMAGES is None:
        _GLANCE_IMAGES = {}
        add_args = []
        tenant_msg = 'Using %s environment variable to filter image list'
        if 'OS_TENANT_ID' in os.environ:
            vprint(tenant_msg % 'OS_TENANT_ID')
            add_args = ['--owner', os.environ['OS_TENANT_ID']]
        elif 'OS_TENANT_NAME' in os.environ:
            vprint(tenant_msg % 'OS_TENANT_NAME')
            cmd = ['keystone', 'tenant-get', os.environ['OS_TENANT_NAME']]
            status, _, out, _ = utils.run(cmd, out=True)
            if status:
                _, block, _, _ = openstack_out.parse_block(out)
                for prop, val in block:
                    if prop == 'id':
                        add_args = ['--owner', val]
                        break
        for imgid in glance.glance_ids(None, *add_args):
            img = glance.glance_show(imgid)
            if img:
                vmmap = openstack_out.map_block(img)
                if 'mpid' in vmmap:
                    vprint(("Found 'mpid' property (%(mpid)s) already set on " +
                            "image: %(id)s (%(name)s)") % vmmap)
                    _GLANCE_IMAGES[vmmap['mpid']] = vmmap
                _GLANCE_IMAGES[vmmap['checksum']] = vmmap
                _GLANCE_IMAGES[vmmap['name']] = vmmap
    return _GLANCE_IMAGES

def get_meta_file(mpid, metadata_url_base):
    '''Retrieve image metadata from StratusLab marketplace, in XML format
    '''
    # Get XML metadata file from StratusLab marketplace
    url_meta = metadata_url_base + mpid
    fn_meta = glancing.get_url(url_meta)
    if not fn_meta:
        vprint("Cannot retrieve XML metadata from URL: " + url_meta)
        return None
    os.rename(fn_meta, fn_meta + '.xml')
    return fn_meta + '.xml'

def needs_upgrade(mpid, old, new, meta_file):
    '''Handle an image already put in glance in a previous run
    '''
    old_md5 = old['checksum']
    old_name = old['name']
    old_ver = old['version']

    new_md5 = new['checksums']['md5']
    new_name = new['title']
    new_ver = new['version']

    if new_md5 == old_md5:
        vprint("Same image: same md5, no upload")
        update_properties(mpid, old, new)
    else:
        vprint("md5 differ")
        if new_ver > old_ver:
            vprint("New image version")
            if not glance.glance_rename(old_name, old_name + '_old'):
                vprint('Warning: Cannot rename old image, will need manual '
                       'intervention')
            vprint("Previous image renamed to: " + old_name + '_old')
            upload_image(mpid, new_name, meta_file)
            update_properties(mpid, old, new)
        elif new_ver < old_ver:
            vprint("NO-OP: downgraded image")
        else:
            vprint("NO-OP: corrupted image (same version, md5 differ)")

def upload_image(mpid, name, meta_file):
    '''Upload new image into glance registry, using metadata file content
    '''
    vprint("Uploading new image: %s (%s)" % (mpid, name))
    ret = glancing.main(['-v', '-n', name, meta_file])
    # Invalidate glance image cache
    # TODO: maybe just add the new one
    global _GLANCE_IMAGES
    _GLANCE_IMAGES = None
    return ret

def set_properties(mpid, new):
    '''Set image properties unconditionnally, accordingly to 'new' metadata
    '''
    vprint("Setting initial image properties for: " + mpid)
    props = []
    vprint("Setting name")
    props.extend(['--name', new['title']])
    vprint("Setting version")
    props.extend(['--property', 'version=' + new['version']])
    vprint("Setting mpid")
    props.extend(['--property', 'mpid=' + mpid])
    ret = glance.glance_update(new['title'], *props)
    if not ret:
        vprint("Could not set properties for image: ", mpid)
    return ret

def update_properties(mpid, old, new):
    '''Update image properties as needed, accordingly to 'old' & 'new' metadata
    '''
    vprint("Updating image properties: " + mpid)
    props = []
    if old['name'] != new['title']:
        vprint("Updating name")
        props.extend(['--name', new['title']])
    if old['version'] != new['version']:
        vprint("Updating version")
        props.extend(['--property', 'version=' + new['version']])
    if ('mpid' not in old) or (old['mpid'] != mpid):
        vprint("Updating mpid")
        props.extend(['--property', 'mpid=' + mpid])
    if props:
        if not glance.glance_update(old['id'], *props):
            vprint("Could not set image properties for: ", mpid)
            return False
    else:
        vprint("NO-OP: All properties have the right values")
    return True

def handle_vm(mpid, url):
    '''Handle one image given by its SL marketplace ID
    '''
    vprint('Handle image with marketplace ID : %s' % mpid)

    meta_file = get_meta_file(mpid, url)
    if meta_file is None:
        return

    # TODO: delete meta_file to avoid filling /tmp

    new = metadata.MetaStratusLabXml(meta_file).get_metadata()
    vmmap = get_glance_images()

    if mpid in vmmap:
        vprint("Image is already in glance")
        needs_upgrade(mpid, vmmap[mpid], new, meta_file)
        # TODO: check other image properties, they should match perfectly
    else:
        vprint("No image with the same marketplace ID found in glance")

        new_md5 = new['checksums']['md5']
        new_name = new['title']
        new_ver = new['version']

        if new_md5 in vmmap:
            vprint('An image with the same MD5 is already in glance')

            old = vmmap[new_md5]

            old_md5 = old['checksum']
            old_name = old['name']
            old_ver = old.get('version', None)

            diff = False

            # Check name
            if old_name != new_name:
                vprint("Names differ, old: %s, new: %s" % (old_name, new_name))
                diff = True

            # Check Version
            if old_ver != new_ver:
                vprint("Versions differ, old: %s, new: %s" % (old_ver, new_ver))
                diff = True

            # Which one is the good one ? Let the admin sort it out...
            if diff:
                diff_msg = "differ, but we don't know which is the good one"
            else:
                diff_msg = "look like the same images"
            vprint("They %s, ignoring..." % diff_msg)

            return

        elif new_name in vmmap:
            old = vmmap[new_name]

            old_md5 = old['checksum']
            old_name = old['name']
            old_ver = old['version']

            vprint('An image with the same name is already in glance: ' +
                   old_name)

            diff = False
            err_msg = "But %s differ, old: %s, new: %s"

            # Check MD5
            if old_md5 != new_md5:
                vprint(err_msg % ("checksums", old_md5, new_md5))
                diff = True

            # Check Version
            assert isinstance(old_ver, int)
            assert isinstance(new_ver, int)
            if old_ver != new_ver:
                vprint(err_msg % ("versions", old_ver, new_ver))
                diff = True
                if old_ver > new_ver:
                    vprint("Versions are going backwards, that's not good.")
                    vprint("Ignoring, fix the image on the market place.")
                    return

            # This should not happen, as it should already have been caught by
            # earlier MD5 checking...
            if not diff:
                vprint("Identical images, that should not happen, please report"
                       " as a bug.")
                return

            if 'mpid' in old:
                vprint("Previous image has 'mpid' property set, "
                       "keeping it as-is...")

            # Backup old image by renaming
            if not glance.glance_rename(old_name, old_name + '_old'):
                vprint('Cannot rename old image, aborting update...')
                return

            vprint("Previous image renamed to: " + old_name + '_old')

        ret = upload_image(mpid, new_name, meta_file)
        if ret:
            ret = set_properties(mpid, new)
        return ret

def main(sys_argv=sys.argv[1:]):
    '''Download images specified in the given list & store them in glance
    '''
    args = do_argparse(sys_argv)
    vprint('Image list(s): ' + str(args.vmlist))
    if not args.vmlist:
        vprint('No image list specified')
        return False
    for img_list_file in args.vmlist:
        if not os.path.exists(img_list_file):
            vprint('Cannot access image list file: ' + img_list_file)
            return False
    vmlist = get_vmlist(args.vmlist)
    for vmid in vmlist:
        vmid = vmid.strip()
        if vmid:
            handle_vm(vmid, args.url)
    return True

if __name__ == '__main__': # pragma: no cover
    main()
