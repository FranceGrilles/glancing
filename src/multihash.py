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

'''Two classes implementing checksum computations with different methods:
- parallel block computation with python's hashlib
- sequential computation by execution of external programs, such as md5sum
  and its cousins.

For big files, parallel hashlib implementation beats serialized execution,
because the source file is only read once. It will also be nicer for the
operating system caches...
'''

import os
import sys
import hashlib
import argparse
import textwrap
import collections

import utils
from utils import vprint

try:
    _HASH_ALGOS = hashlib.algorithms
except AttributeError: # pragma: no cover
    _HASH_ALGOS = hashlib.algorithms_guaranteed

_HLD = hashlib.__dict__

# Mapping from algorithm to digest length
_HASH_TO_LEN = {
    hash_name: _HLD[hash_name]().digest_size * 2 for hash_name in _HASH_ALGOS
}

def hash2len(ahash):
    return _HASH_TO_LEN[ahash]

# Mapping from digest length to algorithm
_LEN_TO_HASH = {
    _HLD[hash_name]().digest_size * 2: hash_name for hash_name in _HASH_ALGOS
}

def len2hash(alen):
    return _LEN_TO_HASH[alen]

class multihash_hashlib(object):
    '''Compute multiple message digests in parallel, using python's hashlib
    '''

    def __init__(self, hash_names=_HASH_ALGOS, block_size=4096):
        self.data = {hash_name: _HLD[hash_name]() for hash_name in hash_names}
        self.block_size = block_size

    def update(self, data):
        for algo in self.data.values():
            algo.update(data)

    def hexdigests(self):
        return {hash_name: hash_obj.hexdigest() for hash_name, hash_obj in self.data.iteritems()}

    def hash_file(self, filename):
        utils.block_read_filename(filename, self.update, self.block_size)

class multihash_serial_exec(object):
    '''Compute multiple message digests, one at a time, using external programs
    '''

    def __init__(self, hash_names=_HASH_ALGOS):
        self.hexdigests_data = {hash_name: '' for hash_name in hash_names}

    def hexdigests(self):
        return self.hexdigests_data

    def hash_file(self, filename):
        if not os.path.exists(filename):
            raise IOError('[Errno 2] No such file or directory: ' + filename)
        for hash_name in self.hexdigests_data.keys():
            ahash = self.get_hash(filename, hash_name)
            self.hexdigests_data[hash_name] = ahash

    @staticmethod
    def get_hash(filename, hash_name):
        """Compute message digest of filename's content with the given hash_name
        algorithm
        """
        cmd = [hash_name + 'sum', '--binary', filename]
        status, _, out, _ = utils.run(cmd, out=True)
        if status:
            return out[:_HASH_TO_LEN[hash_name]]
        return None

def multisum(digs, args):
    '''Emulate md5sum & its family, but computing all the message
       digests in parallel, only reading each file once.
    '''
    data = collections.OrderedDict()
    for (filename, digests) in digs.iteritems():
        for (hash_alg, digest) in digests.iteritems():
            fname = hash_alg.upper() + 'SUMS'
            lst_files = data.get(fname, [])
            lst_files.append(digest + '  ' + filename + '\n')
            data[fname] = lst_files
    for (filename, lines) in data.iteritems():
        vprint('Writing file: ' + filename)
        if not args.force and os.path.exists(filename):
            raise ValueError('ERROR: file already exists:', filename)
        filename = os.path.join(args.directory, filename)
        with open(filename, 'wb') as fout:
            fout.writelines(lines)

# Handle CLI options
def do_argparse(sys_argv):
    desc_help = textwrap.dedent('''
        Emulate md5sum, sha1sum, etc... as if all were run in parallel...
    ''')
    parser = argparse.ArgumentParser(description=desc_help,
                                     formatter_class=utils.AlmostRawFormatter)

    parser.add_argument('-d', '--directory', default='.',
                        help='Directory where checksums files are output')

    parser.add_argument('-f', '--force', action='store_true',
                        help='Overwrite checksum files')

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Display additional information')

    parser.add_argument(dest='files', nargs='+',
                        help='files to comute checksums of')

    args = parser.parse_args(sys_argv)

    if args.verbose:
        utils.set_verbose(True)
        vprint('verbose mode')

    return args

def doit(file_args):
    ret = collections.OrderedDict()
    for arg in file_args:
        mhash = multihash_hashlib()
        mhash.hash_file(arg)
        ret[arg] = mhash.hexdigests()
    return ret

def main(sys_argv=sys.argv[1:]):
    args = do_argparse(sys_argv)
    multisum(doit(args.files), args)

if __name__ == '__main__': # pragma: no cover
    main()
