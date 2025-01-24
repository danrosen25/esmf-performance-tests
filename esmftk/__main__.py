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
import sys
# local
from .testsuite import RunTestSuite

if sys.version_info < (3, 9):
    raise Exception("Python 3.9 or higher is required.")
rc = RunTestSuite(sys.argv[1:])
sys.exit(rc)
