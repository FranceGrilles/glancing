#! /usr/bin/env python

import os
import sys

def mod_path():
    file_myself = __file__ or sys.argv[0]
    ret_path = os.path.dirname(file_myself)
    if not os.path.isabs(ret_path):
        ret_path = os.path.join(os.getcwd(), ret_path)
    return os.path.realpath(ret_path)

def get_local_path(*args):
    return os.path.realpath(os.path.join(mod_path(), *args))

def local_pythonpath(*args):
    local_path = get_local_path(*args)
    if local_path not in sys.path:
        sys.path.append(local_path)
