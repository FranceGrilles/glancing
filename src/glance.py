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
import sys
import argparse

import utils
import openstack_out

from utils import vprint, vprint_lines

_GLANCE_CMD = ['glance']

# Check glance availability early
def glance_ok():
    return glance_run(quiet=True) is not None

# Import VM image into glance
def glance_import_id(base, md5=None, name=None, diskformat=None):
    g_args = None
    args = ['--container-format', 'bare', '--file', base]
    if diskformat is not None:
        args += ['--disk-format', diskformat]
    if name is not None:
        args += ['--name', name]
    if md5 is not None:
        args += ['--checksum', md5]
        # Passing in the checksum has been deprecated in API v2.x
        g_args = ['--os-image-api-version', '1']
    err_msg = 'failed to import image into glance: %s from %s' % (name, base)
    out = glance_run('image-create', glance_args=g_args, subcmd_args=args,
                     err_msg=err_msg)
    if out:
        _, block, _, _ = openstack_out.parse_block(out)
        for property_name, value in block:
            if property_name == 'id':
                return value
    return False

def glance_import(base, md5=None, name=None, diskformat=None):
    return bool(glance_import_id(base, md5, name, diskformat))

def glance_exists(name):
    if not isinstance(name, (str, unicode)):
        vprint('glance_exists(name=%s): name is not a string, but a %s' %
               (name, str(type(name))))
        raise TypeError
    return len(glance_ids([name])) > 0

def glance_run(glance_cmd=None, glance_args=None, subcmd_args=None, **kwargs):
    cmd = list(_GLANCE_CMD)
    if glance_args is not None:
        cmd.extend(glance_args)
    # Handle site-specific parameters (for example: "--insecure")
    os_params = os.environ.get('OS_PARAMS', None)
    if os_params:
        cmd[1:1] = os_params.split()
    if glance_cmd is not None:
        cmd += [glance_cmd]
    if subcmd_args is not None:
        cmd.extend(subcmd_args)
    status, _, out, err = utils.run(cmd, out=True, err=True)
    if not status:
        if not kwargs.get('quiet') is True:
            err_msg = kwargs.get('err_msg', 'failed to run "%s"' % glance_cmd)
            vprint(err_msg)
            if glance_args is not None:
                vprint('glance_args: %s' % str(glance_args))
            if subcmd_args is not None:
                vprint('subcmd_args: %s' % str(subcmd_args))
            vprint_lines('stdout=' + out)
            vprint_lines('stderr=' + err)
        return None
    return out

def glance_ids(names=None, *args):
    ret = set()
    # Single name ?
    if names is not None and isinstance(names, (str, unicode)):
        names = [names]
    imglist = glance_run('image-list', glance_args=None, subcmd_args=args)
    if imglist:
        _, block, _, _ = openstack_out.parse_block(imglist)
        for image_id, image_name in block:
            # Filtering or not ?
            if (names is None or (utils.is_iter(names) and
                                  (image_name in names or image_id in names))):
                ret.add(image_id)
    return ret

def glance_id(name):
    # FIXME: We don't handle images with uuid as name
    if utils.is_uuid(name):
        return name
    name = glance_ids(name)
    # In case of multiple images, only do the first one
    if name and len(name) > 0:
        return list(name)[0]
    # Non-existent image
    return None

def glance_delete_all(names, quiet=False):
    ret = False
    all_images_ids = glance_ids(names)
    if all_images_ids:
        ret = glance_delete_ids(all_images_ids, quiet=quiet)
    return ret

def glance_delete_ids(ids, quiet=False):
    ret = True
    for image_id in ids:
        if len(image_id) > 0:
            ret &= glance_delete(image_id, quiet=quiet)
        else:
            vprint('Error: attempting to delete image with empty ID')
            ret = False
    return ret

def glance_show(name, quiet=False):
    imgid = glance_id(name)
    if imgid is None:
        return False
    err_msg = 'failed to get infos from glance for image: ' + str(imgid)
    out = glance_run('image-show', glance_args=None, subcmd_args=[imgid],
                     err_msg=err_msg, quiet=quiet)
    return out

def glance_delete(name, quiet=False):
    imgid = glance_id(name)
    if imgid is None:
        return False
    err_msg = 'failed to delete image from glance: ' + str(imgid)
    out = glance_run('image-delete', glance_args=None, subcmd_args=[imgid],
                     err_msg=err_msg, quiet=quiet)
    return out is not None

def glance_download(name, fn_local):
    imgid = glance_id(name)
    if imgid is None:
        return False
    err_msg = 'failed to download image from glance: ' + str(imgid)
    out = glance_run('image-download', glance_args=None,
                     subcmd_args=['--file', fn_local, imgid], err_msg=err_msg)
    return out is not None

def glance_rename(vmid, name):
    return glance_update(vmid, '--name', name)

def glance_update(vmid, *args):
    imgid = glance_id(vmid)
    if imgid is None:
        return False
    err_msg = 'failed to update image from glance: ' + str(imgid)
    args = list(args)
    args.append(imgid)
    out = glance_run('image-update', glance_args=None, subcmd_args=args,
                     err_msg=err_msg)
    return out is not None

# Handle CLI options
def do_argparse(sys_argv):
    parser = argparse.ArgumentParser(description='Manage glance VM images')

    # Global options
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='display additional information')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-d', '--delete', dest='delete', metavar='NAME',
                       nargs='+', help='delete all images with the same '
                       'name as the specified VM')

    args = parser.parse_args(sys_argv)

    if args.verbose:
        utils.set_verbose(True)
        vprint('verbose mode')

    return args

def main(sys_argv=sys.argv[1:]):
    args = do_argparse(sys_argv)
    if args.delete:
        vprint('Trying to delete: "%s"' % str(args.delete))
        return glance_delete_all(args.delete)
    else:
        vprint('Listing image IDs:')
        all_images_ids = glance_ids()
        if all_images_ids:
            for img_id in all_images_ids:
                print(img_id)
        else:
            vprint('Error: cannot list image IDs')
            return False
    return True

if __name__ == '__main__': # pragma: no cover
    main()
