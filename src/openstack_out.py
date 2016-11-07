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
import argparse

import utils

_RE_SEP_LINE = re.compile(r'^[+-]+$')

def parse_block(block, line_pattern_re=None, line_anti_pattern_re=None):
    garbin = []
    garbout = []
    header = []
    rows = []
    seps = 0
    length = 0
    for line in block.splitlines():
        # Empty line
        if not line:
            continue
        # A separator line
        if _RE_SEP_LINE.match(line):
            seps += 1
            continue
        # Before the table
        if seps == 0:
            garbin.append(line)
            continue
        # After the table
        elif seps == 3:
            garbout.append(line)
            continue
        # Separate the different columns
        line_split = [i.strip() for i in line.split('|')][1:-1]
        ls_len = len(line_split)
        # This line is a header one
        if seps == 1:
            header = line_split
            length = ls_len
        # These are the data, the rows of the table
        else: # if seps == 2:
            # Select good lines
            if line_pattern_re is not None:
                if not line_pattern_re.search(line):
                    continue
            # Deselect wrong lines
            if line_anti_pattern_re is not None:
                if line_anti_pattern_re.search(line):
                    continue
            # Right number of columns ?
            if length == ls_len:
                rows.append(line_split)
            else:
                print('line "%s" has wrong number of columns %d, should'
                      ' be %d ' % (line, ls_len, length))
                continue

    return header, rows, garbin, garbout

def map_block(block, key_index=0):
    # Be careful, key index has to map to a unique identifer or else
    # you'll lose data: only the last row will be kept...
    ret = {}
    head, pblock, _, _ = parse_block(block)
    # Only two columns: direct mapping
    if len(head) == 2:
        for bline in pblock:
            ret[bline[key_index]] = bline[1]
    # More than two columns: map to lists
    else: # if len(head) > 2:
        for bline in pblock:
            ret[bline[key_index]] = (bline[:key_index] + bline[key_index+1:])
    return ret

def cli(sys_argv=sys.argv[1:]):
    if not sys_argv:
        return None

    desc_help = 'Select a part of an openstack command output'
    parser = argparse.ArgumentParser(description=desc_help)

    parser.add_argument('-s', '--separator', dest='sep', default='',
                        metavar='STRING',
                        help='field separator for output, when there are'
                        'multiple columns')

    parser.add_argument('-p', '--pattern', dest='pattern',
                        metavar='STRING', action='append',
                        help='pattern to select lines. Can be a python'
                        ' regex. Searched in the whole line')

    parser.add_argument('-P', '--anti-pattern', dest='antipattern',
                        metavar='STRING', action='append',
                        help='pattern to deselect lines. Can be a python'
                        ' regex. Searched in the whole line')

    parser.add_argument('-c', '--column', dest='columns', default=[],
                        type=int, metavar='NUMBER', action='append',
                        help='column # to get')

    parser.add_argument('-t', '--head', dest='head', default=None,
                        metavar='NUMBER',
                        help='In case of multi line output, get the first N lines')

    parser.add_argument(dest='cmd', nargs="*", metavar='STRING',
                        help='openstack command, as a single or multiple'
                        ' strings')

    return parser.parse_args(sys_argv)

def get_field(args):

    # Lines selection by pattern matching
    pat = None
    if args.pattern:
        pat = re.compile('|'.join(args.pattern))

    # Lines deselection
    apa = None
    if args.antipattern:
        apa = re.compile('|'.join(args.antipattern))

    cmd = args.cmd
    if len(cmd) > 0:
        # Command to run, simple or multiple strings
        if len(cmd) == 1 and isinstance(cmd[0], str):
            cmd = cmd[0].split()

        # Handle site-specific parameters (for example: "--insecure")
        os_params = os.environ.get('OS_PARAMS', None)
        if os_params:
            cmd[1:1] = os_params.split()
        # Run it, grab output
        status, _, out, _ = utils.run(cmd, out=True)
        if not status:
            return None
    else:
        # No command to run, assume data comes from stdin
        out = sys.stdin.read()

    # Parse the returned array
    if not out:
        return None

    headers, rows, _, _ = parse_block(out, pat, apa)

    # Lines selection by quantity (the first N lines or all of them)
    head = int(args.head) if args.head else len(rows)

    # Column selection
    if not args.columns:
        args.columns = (0,)

    # Return the requested columns
    if len(headers) > max(args.columns):
        return [[row[col] for col in args.columns] for row in rows[:head]]

    return None

def main(sys_argv=sys.argv[1:]):
    # Handle CLI arguments
    args = cli(sys_argv=sys_argv)

    for field in get_field(args):
        print(args.sep.join(str(fent) for fent in field))

if __name__ == '__main__': # pragma: no cover
    main()
