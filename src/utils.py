#! /usr/bin/env python

from __future__ import print_function

import os
import sys
import types
import inspect
import StringIO
import subprocess
import collections

from contextlib import contextmanager

if 'DEVNULL' not in dir(subprocess):
    subprocess.DEVNULL = open(os.devnull, 'rw+b')

_VERBOSE = False

def set_verbose(v=None):
    global _VERBOSE
    if v is None:
        _VERBOSE = not _VERBOSE
    else:
        _VERBOSE = True if v else False

def get_verbose():
    global _VERBOSE
    return _VERBOSE

def vprint(msg, prog=sys.argv[0]):
    if _VERBOSE:
        print("%s: %s" % (prog, msg))

def test_name():
    return inspect.stack()[1][3]

def run(cmd, out=False, err=False):
    stdout = subprocess.PIPE if out else subprocess.DEVNULL
    stderr = subprocess.PIPE if err else subprocess.DEVNULL
    stdoutdata, stderrdata = None, None
    try:
        subp = subprocess.Popen(cmd, stdin=subprocess.DEVNULL,
                                stdout=stdout, stderr=stderr)
        stdoutdata, stderrdata = subp.communicate()
        return subp.returncode == 0, subp.returncode, stdoutdata if out else None, stderrdata if err else None
    except OSError as e:
        vprint("'%s': Cannot execute, please check it is properly"
               " installed, and available through your PATH environment "
               "variable." % (cmd[0],))
        vprint(e)
    return False, None, None, None

class redirect(object):

    def __init__(self, iodesc_name, iofile=None):
        # Prepare
        self._oldiodesc_name = iodesc_name
        if iofile is None:
            self._opened = True
            self._iofile = open(os.devnull, 'w+b')
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

    def __init__(self, iodesc_name):
        super(devnull, self).__init__(iodesc_name, None)

class environ(object):

    def __init__(self, envvar_name, envvar_val=''):
        # Prepare
        self._envvar_name = envvar_name
        self._envvar_val = envvar_val
        self._not_present = False

    def __enter__(self):
        # Backup current state
        if self._envvar_name not in os.environ:
            self._not_present = True
        else:
            self._old_envvar_val = os.environ[self._envvar_name]
        # Modify
        os.environ[self._envvar_name] = self._envvar_val

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore
        if self._not_present:
            del os.environ[self._envvar_name]
        else:
            os.environ[self._envvar_name] = self._old_envvar_val

class cleanup(object):

    def __init__(self, cleanup_cmd):
        # Prepare
        self._cleanup_cmd = cleanup_cmd

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore
        run(self._cleanup_cmd)

class stringio(object):

    def __init__(self):
        self._iofile = StringIO.StringIO()

    def __enter__(self):
        return self._iofile

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._iofile.close()

class Exceptions(object):

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
            if (item.__class__ == other.__class__ and
               item.args == other.args):
                return True
        return False
