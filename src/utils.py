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
import re
import sys
import uuid
import math
import shutil
import inspect
import argparse
import tempfile
import textwrap
import functools
import subprocess
import collections

try:
    import StringIO
except ImportError: # pragma: no cover
    import io as StringIO

if 'DEVNULL' not in dir(subprocess):
    subprocess.DEVNULL = open(os.devnull, 'r+b')

_VERBOSE = False

def set_verbose(verbose=None):
    global _VERBOSE
    if verbose is None:
        _VERBOSE = not _VERBOSE
    else:
        _VERBOSE = True if verbose else False

def get_verbose():
    return _VERBOSE

def vprint(msg, prog=sys.argv[0]):
    if _VERBOSE:
        print("%s: %s" % (prog, msg))

def vprint_lines(msg, prog=sys.argv[0]):
    for line in msg.split('\n'):
        vprint(line, prog=prog)

def test_name():
    return inspect.stack()[1][3]

def is_uuid(thing):
    if isinstance(thing, uuid.UUID):
        return True
    try:
        uuid.UUID(thing)
        return True
    except Exception:
        pass
    return False

def is_iter(thing):
    try:
        iter(thing)
        return True
    except TypeError:
        pass
    return False

class abstract_size_t(object):

    def __init__(self, n, suffix='', unit=None):
        self.n, self._n = n, n
        self.suffix = suffix
        self.unit = ''
        self.shift = 0
        self.around = math.ceil if self._FRACTIONAL else math.floor
        iuf = self._INTERUNIT_FACTOR
        if unit is not None and n != 0:
            self.unit = unit
            self.shift = self._UNIT_PREFIX.index(unit)
            self.n *= self._BASE ** (iuf * self.shift)
        if self.n == 0:
            self.exp = 0
        else:
            self.exp = abs(int(self.around(self._log(self.n) / iuf)))
        if self._FRACTIONAL and type(self._n) == float:
            self.n *= self._BASE ** (iuf * self.exp)
            digits = abs(int(math.floor(self._log(self._n))))
            self.fmt = '%1.' + str(digits) + 'f%s%s'
        else:
            self.n /= self._BASE ** (iuf * self.exp)
            self.fmt = '%d%s%s'

    def _log(self, n):
        return math.log(n, self._BASE)

    def __repr__(self):
        '''Represents the size_t with its construction-time passed parameters'''
        return (('<%s ' + self.fmt + '>') %
                (self.__class__.__name__, self._n, self.unit, self.suffix))

    def __str__(self):
        '''Represents the size_t with "optimized" units (for example: 1024KB => 1MB'''
        return '%d%s%s' % (self.n, self._UNIT_PREFIX[self.exp], self.suffix)

class size_t(abstract_size_t):
    '''This is not a S.I. compliant prefix, this is power-of-two based'''
    _UNIT_PREFIX = ['', 'K', 'M', 'G', 'T', 'P']
    _FRACTIONAL = False
    _INTERUNIT_FACTOR = 10
    _BASE = 2

class small_size_t(abstract_size_t):
    '''3 significative digits
    does not strip trailing zeroes
    string representation may be subject to default 6 digits precision
    '''

    _UNIT_PREFIX = ['', 'm', 'μ', 'n', 'p', 'f']
    _FRACTIONAL = True
    _INTERUNIT_FACTOR = 3
    _BASE = 10

    # For better accuracy than math.log(n, 10)
    def _log(self, n):
        return math.log10(n)

def output(out, quiet):
    if out:
        stdout = subprocess.PIPE
    elif quiet is None or quiet is True:
        stdout = subprocess.DEVNULL
    else:
        stdout = None
    return stdout

def run(cmd, out=False, err=False, quiet_out=None, quiet_err=None):
    stdout = output(out, quiet_out)
    stderr = output(err, quiet_err)
    stdoutdata, stderrdata = None, None
    try:
        subp = subprocess.Popen(cmd, stdin=subprocess.DEVNULL,
                                stdout=stdout, stderr=stderr)
        stdoutdata, stderrdata = subp.communicate()
        return (subp.returncode == 0, subp.returncode,
                stdoutdata if out else None, stderrdata if err else None)
    except OSError as exc:
        vprint("'%s': Cannot execute, please check it is properly"
               " installed, and available through your PATH environment "
               "variable." % (cmd[0],))
        vprint(exc)
    return False, None, None, None

class chdir(object):
    """Context manager that change the current working directory, run
    the code block and then get back to its previous cwd before exiting
    the context.
    """

    def __init__(self, dir_path):
        if not os.path.isdir(dir_path):
            raise ValueError('Not a directory')
        self.oldcwd = None
        self.dir_path = dir_path

    def __enter__(self):
        self.oldcwd = os.getcwd()
        os.chdir(self.dir_path)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.oldcwd)

class tempdir(chdir):
    """Context manager that run the code block in a temporary folder that
    is destroyed before context exits.
    """

    def __init__(self, prefix='glancing-'):
        super(tempdir, self).__init__(tempfile.mkdtemp(prefix=prefix))

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(tempdir, self).__exit__(exc_type, exc_val, exc_tb)
        shutil.rmtree(self.dir_path)

class redirect(object):
    """Context manager to redirect some std stream temporarily to
    another opened file.

    with open('/path/to/output.txt', 'wb') as fout:
        with redirect('stdout', fout):
            print('Hello world !')
    """

    def __init__(self, iodesc_name, iofile=None):
        # Prepare
        self._oldiodesc_name = iodesc_name
        self._oldiodesc = None
        if iofile is None:
            self._opened = True
            self._iofile = open(os.devnull, 'r+b')
        else:
            self._opened = False
            self._iofile = iofile

    def __enter__(self):
        # Backup
        self._oldiodesc = sys.__dict__[self._oldiodesc_name]
        # Modify
        sys.__dict__[self._oldiodesc_name] = self._iofile

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup
        if self._opened:
            self._iofile.close()
        # Restore
        sys.__dict__[self._oldiodesc_name] = self._oldiodesc

class devnull(redirect):
    """Context manager to silence some std stream.

    # Equivalent to: "command > /dev/null"
    with devnull('stdout'):
        command()

    # Equivalent to: "command 2> /dev/null"
    with devnull('stderr'):
        command()
    """

    def __init__(self, iodesc_name):
        super(devnull, self).__init__(iodesc_name, None)

class environ(object):
    """Context manager to manipulate safely the environment variables,
    they'll get back their old values after the context is exited.
    """

    def __init__(self, envvar_name, envvar_val=None):
        # Prepare
        self._envvar_name = envvar_name
        self._envvar_val = envvar_val
        self._not_present = False
        self._old_envvar_val = None

    def __enter__(self):
        # Backup current state
        if self._envvar_name not in os.environ:
            self._not_present = True
        else:
            self._old_envvar_val = os.environ[self._envvar_name]
        # Modify
        if self._envvar_val is None:
            if not self._not_present:
                del os.environ[self._envvar_name]
        else:
            os.environ[self._envvar_name] = self._envvar_val

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore
        if self._not_present:
            if self._envvar_name in os.environ: # ou alors : self._envvar_val is not None
                del os.environ[self._envvar_name]
        else:
            os.environ[self._envvar_name] = self._old_envvar_val

class cleanup(object):
    """Context manager that runs an external command or python code as a cleanup
    action before it exits its enclosing context.
    """

    def __init__(self, cleanup_cmd, *args, **kwargs):
        # Prepare
        self.cleanup_cmd = cleanup_cmd
        self.args = args
        self.kwargs = kwargs

    def _cleanup(self):
        if is_iter(self.cleanup_cmd):
            run(self.cleanup_cmd, quiet_err=False)
        else:
            # TODO/TOTEST: Be consistent with the above run() call
            #self.kwargs['quiet_err'] = False
            self.cleanup_cmd(*self.args, **self.kwargs)

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore
        self._cleanup()

class clean(cleanup):
    """Same as the "cleanup" class, but also run the cleanup action
    before entering the context.
    """

    def __enter__(self):
        self._cleanup()

class stringio(object):
    """StringIO context manager, same as:
    with open("/path/to/fop.txt", "r") as fop:
        do_something_with(fop)
    """

    def __init__(self, data=None):
        if data is not None:
            self._iofile = StringIO.StringIO(data)
        else:
            self._iofile = StringIO.StringIO()

    def __enter__(self):
        return self._iofile

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._iofile.close()

def block_read_filename(filename, callback, block_size=4096):
    """Open and then read a file in chunks, and call a function back for
    each block.
    """
    if block_size < 1:
        raise IOError('Wrong block_size')
    with open(filename, 'rb') as fin:
        block_read_filedesc(fin, callback, block_size)

def block_read_filedesc(filedesc, callback, block_size=4096):
    """Read a file in chunks, and call a function back for each block
    """
    if block_size < 1:
        raise IOError('Wrong block_size')
    chunk_reader = functools.partial(filedesc.read, block_size)
    for block in iter(chunk_reader, ''):
        callback(block)

class Exceptions(object):
    """Class to match an exception's type and its args against a list of
    other exceptions

    excs = utils.Exceptions(
        ZeroDivisionError('integer division or modulo by zero'),
        ArithmeticError('integer division or modulo by zero'),
    )

    try:
        0 / 0
    except Exception as e:
        if e in excs:
            print('Learn your math lessons')
        else:
            raise e
    """

    def __init__(self, *args):
        if len(args) == 1 and isinstance(args[0], collections.Iterable):
            keys = args[0]
        else:
            keys = args
        self._excs = []
        for item in keys:
            if type(item) == type(Exception):
                item = item()
            if isinstance(item, Exception):
                self._excs.append(item)

    def __contains__(self, other):
        for item in self._excs:
            if item.__class__ == other.__class__ and item.args == other.args:
                return True
        return False

class AlmostRawFormatter(argparse.HelpFormatter):
    '''Useful for multiline argparse option descriptions

    Based on code from:
    http://dolinked.com/questions/12720/python-argparse-how-to-insert-newline-the-help-text
    '''
    _PREFIX = '>>>'

    def _split_lines(self, text, width):
        if text.strip().startswith(self._PREFIX):
            dedented = textwrap.dedent(text[len(self._PREFIX):])
            return dedented.strip().splitlines()
        return super(AlmostRawFormatter, self)._split_lines(text, width)

def alphanum_sort(iterable, prefix='', suffix=''):
    '''
    Used to sort list of seemingly identical strings:

    sbgcsrv4.in2p3.fr              sbgcsrv1.in2p3.fr
    sbgcsrv06.in2p3.fr             sbgcsrv4.in2p3.fr
    sbgcsrv1.in2p3.fr      =>      sbgcsrv06.in2p3.fr
    sbgcsrv7.in2p3.fr              sbgcsrv7.in2p3.fr
    sbgcsrv13.in2p3.fr             sbgcsrv13.in2p3.fr
    '''

    res = {}
    bad = []
    for item in iterable:
        if not item.startswith(prefix):
            bad.append(item)
            continue
        i = item[len(prefix):-len(suffix)]
        if not i:
            idx = -1
        elif '.' in i:
            idx = float(i)
        else:
            idx = int(i)
        res_ = res.get(idx, [])
        res_.append(i)
        res[idx] = res_
    result = []
    # First sort by number value
    for num in sorted(res):
        # Then for identical number values, sort according to string length
        for str_val in sorted(res[num], key=len):
            result.append(prefix + str_val + suffix)
    return result, bad

def tr_s(datastr):
    '''
    Work similarly as the "tr -s" unix command
    '''
    return re.sub(r'(.)(\1+)', r'\1', datastr)
