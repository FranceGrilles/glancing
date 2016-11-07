#! /usr/bin/env python

import os
import sys
import pickle
import timeit
import argparse

import matplotlib.pyplot as plt
import matplotlib.markers

from tutils import local_pythonpath

# Setup project-local PYTHONPATH
local_pythonpath('..', '..', 'src')

import utils

_SETUP = \
'''
import multihash
mh = multihash.multihash_%s(%s)
'''

def bench_one(fname, setup, repeats=1):
    return timeit.timeit('mh.hash_file("%s")' % fname, setup=setup,
                         number=repeats)

def bench_files(files):
    lengths = []
    times_sh = []
    times_mh = {
        # Uninteresting buffer sizes: too small
        32: [],
        64: [],
        128: [],
        512: [],
        1024: [],
        1024 * 4: [],
        1024 * 1024: [],
        10 * 1024 * 1024: [],
    }
    for fname in files:
        lengths.append(os.path.getsize(fname) / (1024 * 1024))
        times_sh.append(bench_one(fname, _SETUP % ('serial_exec', '')))
        for size, res in times_mh.iteritems():
            res.append(bench_one(fname, _SETUP %
                                 ('hashlib', 'block_size=%d' % size)))
    return lengths, times_sh, times_mh

def plotit(lengths, times_sh, times_mh, image_file, display):
    plt.title('Benchmark multiple hash computing implementations')
    plt.xlabel('File size in MB')
    plt.ylabel('Time in seconds')
    plt.rc('lines', linewidth=1, linestyle='-')

    # Prepare marker list
    mks = set(matplotlib.markers.MarkerStyle().markers.keys())
    # Remove unwanted ones
    mks -= set((None, 'None', '', ' ', '|', '_', '.', ',', '+', '-', 'd', 'x', '*'))
    mks = ['<', '>', '^', 'v', 'o', 'D', 's', 'p', 'h', ]
    assert len(mks) >= len(times_mh)

    # Experiment with logarithmic scale
    plotter = plt.semilogx # plt.plot

    # Plot serial exec data
    plotter(lengths, times_sh, label='serial exec', marker='*')

    # Plot parallel hashlib data, for each block size
    for size in sorted(times_mh.keys()):
        plotter(lengths, times_mh[size], marker=mks.pop(),
                label='parallel hashlib, bs=%s' % (utils.size_t(size),))

    # Give some horizontal room
    #xmin, xmax = plt.xlim()
    #plt.xlim(0, xmax * 1.1)

    # Put legend in top left corner
    plt.legend(loc=2)

    # Save an image of the plotted data
    if image_file:
        plt.savefig(image_file)

    # Display resulting figure
    if display:
        plt.show()

def parse_args():
    parser = argparse.ArgumentParser(description='Benchmark multihash')

    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('-l', '--load', dest='load', metavar='FILE',
                       help='load data from specified file')
    group.add_argument('-s', '--store', dest='store', metavar='FILE',
                       help='store data into specified file')

    parser.add_argument(dest='files', metavar='DATAFILE', nargs='*',
                        help='files to compute checksums of')

    parser.add_argument('-d', '--display', dest='display', action='store_true',
                        help='display plot data')
    parser.add_argument('-p', '--plot', dest='plot', metavar='FILE',
                        help='save plot data to .svg image file')

    return parser

def main():
    parser = parse_args()
    args = parser.parse_args()
    if args.load:
        if args.files:
            print "\nIgnoring DATAFILE(s) parameters, loading data from:", args.load
        with open(args.load, 'rb') as fin:
            lengths, times_sh, times_mh = pickle.load(fin)
    else:
        if args.files:
            lengths, times_sh, times_mh = bench_files(args.files)
            if args.store:
                with open(args.store, 'wb+') as fout:
                    pickle.dump((lengths, times_sh, times_mh), fout)
        else:
            parser.print_help()
            print "\nMissing DATAFILE(s) parameters"
            sys.exit(1)

    if args.display or args.plot:
        plotit(lengths, times_sh, times_mh, args.plot, args.display)

if __name__ == '__main__':
    main()
