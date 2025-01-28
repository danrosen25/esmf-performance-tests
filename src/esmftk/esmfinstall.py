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
import hashlib
import os
# local
from .packageout import *

class ESMFInstallation():

    def __init__(self, esmfpath: str, pkgout: PackageOut=None):
        if PackageOut is None:
            self.pkgout = PackageOut()
        else:
            self.pkgout = pkgout
        self.mkfile = None
        if os.path.basename(esmfpath) == 'esmf.mk':
            self.mkfile = os.path.abspath(esmfpath)
            if not os.path.exists(self.mkfile):
                self.pkgout.abort('esmf.mk file not found - ' + esmfpath)
        else:
            for root, dirs, files in os.walk(esmfpath):
                if 'esmf.mk' in files:
                    self.mkfile = os.path.join(root, 'esmf.mk')
                    break
            if self.mkfile is None:
                self.pkgout.abort('esmf.mk file not found - ' + esmfpath)
        self.config = {}
        with open(self.mkfile, "r") as file:
            hasher = hashlib.shake_256()
            for line in file:
                hasher.update(bytes(line, 'utf-8'))
                if line.lstrip().startswith('ESMF_'):
                    key, value = line.split("=", maxsplit=1)
                    self.config[key] = value.rstrip()
        self.mkdigest = hasher.hexdigest(4)
        self.vers = (self.config["ESMF_VERSION_MAJOR"] +
                     "." + self.config["ESMF_VERSION_MINOR"] +
                     "." + self.config["ESMF_VERSION_REVISION"])
        if 'F' in self.config["ESMF_VERSION_PUBLIC"]:
            self.vers += '-dev'

    def setenv(self):
        os.environ["ESMFMKFILE"] = self.mkfile

    def __str__(self):
        msg = ("ESMF Build Information" +
            "\n  Makefile Fragment: " + self.mkfile +
            "\n  Version: " + self.config["ESMF_VERSION_STRING"] +
            "\n  Git Version: " + self.config["ESMF_VERSION_STRING_GIT"] +
            "\n  Public: " + self.config["ESMF_VERSION_PUBLIC"] +
            "\n  Beta Snapshot: " + self.config["ESMF_VERSION_BETASNAPSHOT"] +
            "\n")
        return msg
