#! /usr/bin/env python

from __future__ import print_function

import os
import sys
import urllib
import textwrap
import urlparse
import argparse

import utils
import glance
import multihash
import decompressor
import metadata as md

from utils import vprint

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
                       help='Import image into glance even if checksum verification failed')
    group.add_argument('-d', '--dry-run', dest='dryrun', action='store_true',
                       help='Do not import image into glance')

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Display additional information')

    parser.add_argument('-n', '--name', dest='name', default=None,
                        help='Name of the image in glance registry. Default value derived from image file name.')

    parser.add_argument('-k', '--keep-temps', dest='keeptemps', action='store_true',
                        help='Keep temporary files (VM image & other)')

    digests_help = ('''>>>
        A colon-separated list of message digests of the image.

        This overrides / complements the checksums that are present in
        metadata, if using the StratusLab marketplace.

        Algorithms are deduced from checksum lengths.

        For example, an MD5 (32 chars) and a SHA-1 (40 chars):
        "3bea57666cdead13f0ed4a91beef2b98:1b5229d5dad92bc6662553be01608af2180eafbe"
    ''')
    parser.add_argument('-s', '--sums', dest='digests', help=digests_help)

    descriptor_help = textwrap.dedent('''>>>
        This can be:
          * a local VM image file (in "raw" format)
          * a network location (URL)
          * a StratusLab marketplace ID
          * a StratusLab marketplace metadata file (in JSON or XML format)

        The StratusLab marketplace is located here:

          https://marketplace.stratuslab.eu
    ''')
    parser.add_argument('descriptor', metavar='DESC', help=descriptor_help)

    args = parser.parse_args(sys_argv)

    if args.verbose:
        utils.set_verbose(True)
        vprint('verbose mode')

    return args

# Get uncompressed VM image file from the given url
def get_url(url):
    try:
        fn, hdrs = urllib.urlretrieve(url)
    except IOError as e:
        return None
    return fn

# Check all message digests of the image file
def check_digests(local_image_file, metadata, replace_bads=False):
    verified = 0
    hashes = metadata['checksums']
    mh = multihash.multihash_hashlib(hashes)
    mh.hash_file(local_image_file)
    hds = mh.hexdigests()
    for hashfn in sorted(hashes):
        digest_computed = hds[hashfn]
        digest_expected = hashes[hashfn]
        if digest_computed.lower() == digest_expected.lower():
            verified += 1
            vprint('%s: %s: OK' % (local_image_file, hashfn))
        else:
            vprint('%s: %s: expected: %s' % (local_image_file, hashfn, digest_expected))
            vprint('%s: %s: computed: %s' % (local_image_file, hashfn, digest_computed))
            if replace_bads:
                hashes[hashfn] = digest_computed
    return verified

_BACKUP_DIR = os.path.join('/', 'tmp', 'glancing')

def backup_dir():
    if not os.path.exists(_BACKUP_DIR):
        os.mkdir(_BACKUP_DIR)
    elif not os.path.isdir(_BACKUP_DIR):
        vprint(_BACKUP_DIR + ' exists but is not a direstory, sorry cannot backup old image...')

def main(sys_argv=sys.argv[1:]):

    # Handle CLI arguments
    args = do_argparse(sys_argv)

    # Check glance availability early
    if not args.dryrun and not glance.glance_ok():
        vprint('local glance command-line client problem')
        return False

    # Guess which mode are we operating in
    image_type = None
    d = args.descriptor
    if d.startswith('http://') or d.startswith('https://'):
        image_type = 'url'
    elif os.path.exists(d):
        ext = os.path.splitext(d)[1]
        if ext == '.xml':
            image_type = 'xml'
        elif ext == '.json':
            image_type = 'json'
        else:
            image_type = 'image'
    else:
        image_type = 'market'
        if len(d) != 27:
            vprint('probably invalid StratusLab ID')

    if image_type is None:
        vprint('Cannot guess mode of operation')
        return False

    # Prepare VM image metadata
    if image_type == 'market':
        # Get xml metadata file from StratusLab marketplace
        metadata_url_base = 'https://marketplace.stratuslab.eu/marketplace/metadata/'
        local_metadata_file = get_url(metadata_url_base + args.descriptor)
        metadata = md.MetaStratusLabXml(local_metadata_file).get_metadata()
    elif image_type == 'json':
        metadata = md.MetaStratusLabJson(args.descriptor).get_metadata()
    elif image_type == 'xml':
        metadata = md.MetaStratusLabXml(args.descriptor).get_metadata()
    else:
        metadata = {'checksums': {}, 'format': 'raw'}

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
        if image_type in ('xml', 'json', 'market'):
            url = metadata['location']
        elif image_type == 'url':
            url = args.descriptor
        local_image_file = get_url(url)
        if not local_image_file or not os.path.exists(local_image_file):
            vprint('cannot download from: ' + url)
            return False
        vprint(local_image_file + ': downloaded image from: ' + url)

    # VM images are compressed, but checksums are for uncompressed files
    if 'compression' in metadata and metadata['compression']:
        chext = '.' + metadata['compression']
        d = decompressor.Decompressor(local_image_file, ext=chext)
        d.doit(delete=(not args.keeptemps))
        # Get rid of compression file extention
        local_image_file, ext = os.path.splitext(local_image_file)
        vprint(local_image_file + ': uncompressed file')

    # Choose VM image name
    name = args.name
    if name is None:
        if image_type == 'image':
            name, ext = os.path.splitext(os.path.basename(local_image_file))
        elif image_type == 'url':
            name, ext = os.path.splitext(os.path.basename(urlparse.urlsplit(url)[2]))
        elif image_type in ('xml', 'json', 'market'):
            name = '%s-%s-%s' % (metadata['os'], metadata['os-version'], metadata['os-arch'])
    vprint(local_image_file + ': VM image name: ' + name)

    # Populate metadata message digests to be verified
    if args.digests:
        for dig in filter(None, args.digests.split(':')):
            dig_len = len(dig)
            if dig_len in multihash._LEN_TO_HASH:
                halg = multihash._LEN_TO_HASH[dig_len]
                if halg in metadata['checksums']:
                    if dig == metadata['checksums'][halg]:
                        vprint('duplicate digest, computing only once: ' + dig)
                    else:
                        vprint('conflicting digests: ' + dig + ':' + metadata['checksums'][halg])
                        return False
                else:
                    metadata['checksums'][halg] = dig
            else:
                vprint('unrecognized digest: ' + dig)
                return False

    # Verify image size
    size_ok = True
    if 'bytes' in metadata:
        size_expected = int(metadata['bytes'])
        size_actual = os.path.getsize(local_image_file)
        size_ok = size_expected == size_actual

        if size_ok:
            vprint('%s: size: OK' % (local_image_file,))
        else:
            vprint('%s: size: expected: %d' % (local_image_file, size_expected))
            vprint('%s: size:   actual: %d' % (local_image_file, size_actual))
            if not args.force:
                return False

    # Verify image checksums
    verified = 0
    if size_ok:
        if len(metadata['checksums']) > 0:
            vprint(local_image_file + ': verifying checksums')
            verified = check_digests(local_image_file, metadata, args.force)
        elif image_type not in ('xml', 'json', 'market'):
            vprint(local_image_file + ': no checksum to verify (forgot "-s" CLI option ?)')
        else:
            vprint(local_image_file + ': no checksum to verify found in metadata...')
    else:
        if args.force:
            vprint(local_image_file + ': size differ, but forcing the use of recomputed md5')
            metadata['checksums'] = { 'md5': '0' * 32 }
            check_digests(local_image_file, metadata, args.force)
        else:
            vprint(local_image_file + ': size differ, not verifying checksums')

    # If image already exists, download it to backup directory
    if not args.dryrun and glance.glance_exists(name):
        backup_dir()
        fn_local = os.path.join(_BACKUP_DIR, name)
        ok = glance.glance_download(name, fn_local)
        if not ok:
            return False
        glance.glance_delete(name, quiet=(not utils.get_verbose()))

    # Import image into glance
    if not args.dryrun:
        if (size_ok and len(metadata['checksums']) == verified) or args.force:
            vprint(local_image_file + ': importing into glance as "%s"' % name or '')
            md5 = metadata['checksums'].get('md5', None)
            ret = glance.glance_import(local_image_file, md5, name, metadata['format'])
            if not ret:
                return False
        else:
            return False
    else:
        if not args.force and (not size_ok or not len(metadata['checksums']) == verified):
            return False

    # Keep downloaded image file
    if not image_type == 'image' and not args.keeptemps:
        vprint(local_image_file + ': deleting temporary file')
        os.remove(local_image_file)

    # That's all folks !
    return True

if __name__ == '__main__':
    main()
