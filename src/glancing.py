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

'''Download cloud images, verify their checksums, store them in glance...
'''

from __future__ import print_function

import os
import re
import sys
#import base64
import binascii
import tempfile
import textwrap
import argparse

try:
    from urllib2 import urlopen, URLError, HTTPError
    from urlparse import urlsplit
except ImportError:
    from urllib.request import urlopen
    from urllib.error import URLError, HTTPError
    from urllib.parse import urlsplit

import utils
import glance
import multihash
import decompressor
import metadata as md

from utils import vprint, size_t

# Handle CLI options
def do_argparse(sys_argv):
    desc_help = textwrap.dedent('''
        Import VM images into OpenStack glance image registry.
        Verify checksum(s), image size, etc...
        Backup old images being replaced.
    ''')
    parser = argparse.ArgumentParser(description=desc_help,
                                     formatter_class=utils.AlmostRawFormatter)

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-f', '--force', action='store_true',
                       help=('Import image into glance even if checksum '
                             'verification failed'))
    group.add_argument('-d', '--dry-run', dest='dryrun', action='store_true',
                       help='Do not import image into glance')

    parser.add_argument('-D', '--no-checksum', action='store_true',
                        help='Do not verify checksums', dest='nocheck')

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Display additional information')

    parser.add_argument('-n', '--name', dest='name', default=None,
                        help=('Name of the image in glance registry. Default '
                              'value derived from image file name.'))

    parser.add_argument('-k', '--keep-temps', dest='keeptemps',
                        action='store_true',
                        help='Keep temporary files (VM image & other)')

    parser.add_argument('-c', '--cern-list', dest='cernlist',
                        help='Image list from CERN, as a JSON file')

    parser.add_argument('-b', '--backup-dir', dest='backupdir',
                        help='Backup already existing images in this directory')

    digests_help = ('''>>>
        A colon-separated list of message digests of the image.

        This overrides / complements the checksums that are present in
        metadata, if using the StratusLab marketplace. It also overrides
        checksum files loaded with -S or --sums-files.

        Algorithms are deduced from checksum lengths.

        For example, an MD5 (32 chars) and a SHA-1 (40 chars):
        "3bea57666cdead13f0ed4a91beef2b98:1b5229d5dad92bc6662553be01608af2180eafbe"
    ''')
    parser.add_argument('-s', '--sums', dest='digests', help=digests_help)

    digests_files_help = ('''>>>
        A message digest file to load.

        This overrides / complements the checksums that are present in
        metadata, if using the StratusLab marketplace.

        Algorithms are deduced from checksum lengths.
    ''')
    parser.add_argument('-S', '--sums-files', dest='sums_files', nargs='*',
                        help=digests_files_help)

    descriptor_help = ('''>>>
        This can be:
          * a local file path:
             - to an image file in "raw" format
             - to a StratusLab marketplace metadata file in JSON or XML format
          * a StratusLab marketplace ID
          * a network location (URL)
          * a CERN image list ID, with the VM image list passed in as --cern-list

        The StratusLab marketplace is located here:

          https://marketplace.stratuslab.eu
    ''')
    parser.add_argument('descriptor', metavar='STRING', help=descriptor_help)

    args = parser.parse_args(sys_argv)

    if args.verbose:
        utils.set_verbose(True)
        vprint('verbose mode')

    return args

def get_url(url):
    '''Retrieve content from URL into a temporary file.
       Return temporary file name.
    '''
    if not url or not isinstance(url, (str, unicode)):
        return None
    try:
        url_f = urlopen(url)
    except HTTPError as exc:
        if exc.code == 404 and exc.reason == 'Not Found':
            vprint(str(exc))
            return None
        raise exc
    except URLError as exc:
        vprint(str(exc))
        return None
    except ValueError as exc:
        if exc.args[0] == 'unknown url type: %s' % url:
            # TODO: is this secure enough ? It should only be used for testing
            #       metadata mode
            if not os.path.exists(url):
                return None
            else:
                url_f = open(url, 'r')
                if not url_f:
                    vprint(str(exc))
                    return None
        else:
            raise exc
    with tempfile.NamedTemporaryFile(bufsize=4096, delete=False) as fout:
        try:
            utils.block_read_filedesc(url_f, fout.write, 4096)
        except IOError as exc:
            vprint('cannot write temp file: ' + fout.name)
            os.remove(fout.name)
            return None
    return fout.name

# Add to metadata['checksums'] a new message digest to be verified
def add_checksum(dig, metadata, overrides=False):
    try:
        halg = multihash.len2hash(len(dig))
    except KeyError:
        vprint('unrecognized digest: ' + dig)
        return False
    if halg in metadata['checksums']:
        if dig == metadata['checksums'][halg]:
            vprint('duplicate digest, computing only once: ' + dig)
        elif overrides:
            metadata['checksums'][halg] = dig
        else:
            vprint('conflicting digests: ' + dig + ':' + metadata['checksums'][halg])
            return False
    else:
        metadata['checksums'][halg] = dig
    return True

# Check all message digests of the image file
def check_digests(local_image_file, metadata, replace_bads=False):
    verified = 0
    hashes = metadata['checksums']
    mhash = multihash.multihash_hashlib(hashes)
    mhash.hash_file(local_image_file)
    hds = mhash.hexdigests()
    for hashfn in sorted(hashes):
        digest_computed = hds[hashfn]
        digest_expected = hashes[hashfn]
        if digest_computed.lower() == digest_expected.lower():
            verified += 1
            vprint('%s: %s: OK' % (local_image_file, hashfn))
        else:
            fmt_ex = (local_image_file, hashfn, digest_expected)
            fmt_co = (local_image_file, hashfn, digest_computed)
            vprint('%s: %s: expected: %s' % fmt_ex)
            vprint('%s: %s: computed: %s' % fmt_co)
            if replace_bads:
                hashes[hashfn] = digest_computed
    return verified

def main(sys_argv=sys.argv[1:]):

    # Handle CLI arguments
    args = do_argparse(sys_argv)

    # Check glance availability early
    if not args.dryrun and not glance.glance_ok():
        vprint('local glance command-line client problem')
        return False

    # Guess which mode are we operating in
    image_type = None
    desc = args.descriptor
    vprint('descriptor: ' + desc)
    if desc.startswith('http://') or desc.startswith('https://'):
        image_type = 'url'
    elif os.path.exists(desc):
        ext = os.path.splitext(desc)[1]
        if ext == '.xml':
            image_type = 'xml'
        elif ext == '.json':
            image_type = 'json'
        else:
            image_type = 'image'
    else:
        if args.cernlist:
            image_type = 'cern'
        elif len(desc) == 27:
            try:
                # This was assumed to be SLMP ID encoding format, apparently not
                #base64.decodestring(desc)
                image_type = 'market'
            except binascii.Error:
                vprint('probably invalid StratusLab marketplace ID:', desc)
        else:
            vprint('unknown descriptor')

    if image_type is None:
        vprint('Cannot guess mode of operation')
        return False
    vprint('Image type: ' + image_type)

    # Prepare VM image metadata
    if image_type == 'market':
        # Get xml metadata file from StratusLab marketplace
        metadata_url_base = 'https://marketplace.stratuslab.eu/marketplace/metadata/'
        sl_md_url = metadata_url_base + args.descriptor
        local_metadata_file = get_url(sl_md_url)
        if local_metadata_file is None:
            vprint('cannot get xml metadata file from StratuLab marketplace: ' + sl_md_url)
            return False
        else:
            vprint('downloaded xml metadata file from StratuLab marketplace: ' + sl_md_url)
            vprint('into local file: ' + local_metadata_file)
            meta = md.MetaStratusLabXml(local_metadata_file)
    elif image_type == 'cern':
        meta = md.MetaCern(args.cernlist, args.descriptor)
    elif image_type == 'json':
        meta = md.MetaStratusLabJson(args.descriptor)
    elif image_type == 'xml':
        meta = md.MetaStratusLabXml(args.descriptor)

    if image_type in ('image', 'url'):
        metadata = {'checksums': {}, 'format': 'raw'}
    else:
        metadata = meta.get_metadata()

    # Ensure we have something to work on
    if not metadata:
        vprint('Cannot retrieve metadata')
        return False

    # Retrieve image in a local file
    if image_type == 'image':
        # Already a local file
        local_image_file = args.descriptor
    else:
        # Download from network location
        if image_type in ('xml', 'json', 'market', 'cern'):
            url = metadata['location']
        elif image_type == 'url':
            url = args.descriptor
        local_image_file = get_url(url)
        if not local_image_file or not os.path.exists(local_image_file):
            vprint('cannot download from: ' + url)
            return False
        vprint(local_image_file + ': downloaded image from: ' + url)

    # VM images are compressed, but checksums are for uncompressed files
    compressed = ('compression' in metadata and metadata['compression'] and
                  metadata['compression'].lower() != 'none')
    if compressed:
        chext = '.' + metadata['compression']
        decomp = decompressor.Decompressor(local_image_file, ext=chext)
        res, local_image_file = decomp.doit(delete=(not args.keeptemps))
        if not res:
            vprint(local_image_file + ': cannot uncompress')
            return False
        vprint(local_image_file + ': uncompressed file')

    if image_type == 'image':
        base_name = os.path.basename(local_image_file)
    elif image_type == 'url':
        base_name = os.path.basename(urlsplit(url)[2])

    # Choose VM image name
    name = args.name
    if name is None:
        if image_type in ('image', 'url'):
            name, ext = os.path.splitext(base_name)
        elif image_type in ('xml', 'json', 'market', 'cern'):
            name = meta.get_name()
    vprint(local_image_file + ': VM image name: ' + name)

    # Populate metadata message digests to be verified, from checksum files
    if args.sums_files:
        if image_type in ('xml', 'json', 'market', 'cern'):
            raise NotImplementedError
        else:
            base_fn = base_name
        re_chks_line = re.compile(r'(?P<digest>[a-zA-Z0-9]+)\s+(?P<filename>.+)')
        for sum_file in args.sums_files:
            if sum_file.startswith(('http://', 'https://')):
                local_sum_file = get_url(sum_file)
                if not local_sum_file or not os.path.exists(local_sum_file):
                    vprint('cannot download from: ' + sum_file)
                    return False
                vprint(local_sum_file + ': downloaded checksum file from: ' +
                       sum_file)
                sum_file = local_sum_file
            with open(sum_file, 'rb') as sum_f:
                vprint(sum_file + ': loading checksums...')
                for line in sum_f:
                    match = re_chks_line.match(line)
                    if match and base_fn == match.group('filename'):
                        vprint(sum_file + ': matched filenames: ' + base_fn +
                               ' == ' + match.group('filename'))
                        ret = add_checksum(match.group('digest'), metadata,
                                           overrides=True)
                        if not ret:
                            vprint(sum_file + ': cannot add_checksum(' +
                                   match.group('digest') + ')')
                            return False

    # Populate metadata message digests to be verified, from CLI parameters
    if args.digests:
        digs = [dig for dig in args.digests.split(':') if dig]
        for dig in digs:
            ret = add_checksum(dig, metadata, overrides=True)
            if not ret:
                return False

    # Verify image size
    size_ok = True
    if 'bytes' in metadata:
        size_expected = int(metadata['bytes'])
        size_actual = os.path.getsize(local_image_file)
        size_ok = size_expected == size_actual

        if size_ok:
            vprint('%s: size: OK: %s' % (local_image_file, size_t(size_actual)))
        else:
            vprint('%s: size: expected: %d' % (local_image_file, size_expected))
            vprint('%s: size:   actual: %d' % (local_image_file, size_actual))
            if not args.force:
                return False

    # Verify image checksums
    verified = len(metadata['checksums'])
    if not args.nocheck:
        verified = 0
        if size_ok:
            if len(metadata['checksums']) > 0:
                vprint(local_image_file + ': verifying checksums')
                verified = check_digests(local_image_file, metadata, args.force)
            elif image_type not in ('xml', 'json', 'market', 'cern'):
                vprint(local_image_file +
                       ': no checksum to verify (forgot "-s" CLI option ?)')
            else:
                vprint(local_image_file +
                       ': no checksum to verify found in metadata...')
        else:
            if args.force:
                vprint(local_image_file +
                       ': size differ, but forcing the use of recomputed md5')
                metadata['checksums'] = {'md5': '0' * 32}
                check_digests(local_image_file, metadata, args.force)
            else:
                vprint(local_image_file +
                       ': size differ, not verifying checksums')

    # If image already exists, download it to backup directory prior to deleting
    if not args.dryrun and glance.glance_exists(name):
        if args.backupdir:
            backupdir = args.backupdir
        else:
            backupdir = os.environ.get('GLANCING_BACKUP_DIR', '/tmp/glancing')

        do_backup = True
        if not os.path.exists(backupdir):
            os.mkdir(backupdir)
        elif not os.path.isdir(backupdir):
            vprint(backupdir + ' exists but is not a directory, sorry '
                   'cannot backup old images...')
            do_backup = False

        if do_backup:
            fn_local = os.path.join(backupdir, name)
            status = glance.glance_download(name, fn_local)
            if not status:
                return False
        glance.glance_delete(name, quiet=(not utils.get_verbose()))

    # Import image into glance
    if not args.dryrun:
        if (size_ok and len(metadata['checksums']) == verified) or args.force:
            vprint(local_image_file + ': importing into glance as "%s"' %
                   str(name))
            md5 = metadata['checksums'].get('md5', None)
            ret = glance.glance_import(local_image_file, md5, name,
                                       metadata['format'])
            if not ret:
                return False
        else:
            return False
    else:
        if not args.force and (not size_ok or
                               not len(metadata['checksums']) == verified):
            return False

    # TODO: the following should be done even if something went wrong...

    # Keep downloaded image file
    if not image_type == 'image' and not args.keeptemps:
        vprint(local_image_file + ': deleting temporary file')
        os.remove(local_image_file)

    # That's all folks !
    return True

if __name__ == '__main__': # pragma: no cover
    main()
