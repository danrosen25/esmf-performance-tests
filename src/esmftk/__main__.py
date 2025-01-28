# -*- coding: utf-8 -*-
'''
ESMF TestKit (esmftk)

Copyright (c) 2002-2025 University Corporation for Atmospheric Research,
Massachusetts Institute of Technology, Geophysical Fluid Dynamics Laboratory,
University of Michigan, National Centers for Environmental Prediction, Los
Alamos National Laboratory, Argonne National Laboratory, NASA Goddard Space
Flight Center. All rights reserved.
'''

# standard
import argparse
import sys
# local
from .__init__ import __version__
from .packageout import PackageOut
from .testsuite import TestSuite

def RunTestSuite(argv):

    # read input arguments
    parser = argparse.ArgumentParser(prog=__package__)
    parser.add_argument('testsuite', nargs='?',
        help='YAML configuration file'
    )
    parser.add_argument('--version', action='store_true',
        help='print the version number and exit'
    )
    parser.add_argument('--color', action='store_true',
        help='add color to output',
    )
    args = parser.parse_args()

    if args.version:
        print("ESMF TestKit v" + __version__)
    elif args.testsuite is None:
        parser.error('requires [testsuite]')
    else:
        p = PackageOut(args.color)
        t = TestSuite(args.testsuite, p)
        rc = t.run()
        return rc

if sys.version_info < (3, 9):
    raise Exception("Python 3.9 or higher is required.")
rc = RunTestSuite(sys.argv[1:])
sys.exit(rc)
