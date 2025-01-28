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

class PackageOut():

    colorful=False

    def __init__(self, colorful: bool=None):
        if colorful is None:
            self.colorful = False
        else:
            self.colorful = colorful

    def abort(self, message: str):
        if self.colorful:
            sys.exit('\033[91mERROR: ' + message + '\033[0m')
        else:
            sys.exit('ERROR: ' + message)

    def abortfp(self, message: str, fpath: str, pos: int):
        lcount = 1
        ccount = 1
        index = 0
        with open(fpath, 'r') as file:
            while index < pos:
                char = file.read(1)
                if not char:
                    break
                if char == '\n':
                    ccount = 0
                    lcount += 1
                ccount += 1
                index += 1
        self.abort(message + ' (' +
            fpath + ':' + str(lcount) + ':' + str(ccount) + ')'
        )

    def error(self, message: str):
        if self.colorful:
            print('\033[91mERROR: ' + message + '\033[0m')
        else:
            print('ERROR: ' + message)

    def warning(self, message: str):
        if self.colorful:
            print('\033[93mWARNING: ' + message + '\033[0m')
        else:
            print('WARNING: ' + message)

    def __str__(self):
        return "PackageOut.colorful=" + str(self.colorful)
