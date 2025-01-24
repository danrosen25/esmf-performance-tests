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
from datetime import datetime as dt
import os
import subprocess
# third party
import yaml
# local
from .esmfinstall import *
from .packageout import *
from .testcase import *
from .testresult import *

class TestSuite():

    def __init__(self, filepath: str, pkgout: PackageOut=None):
        if PackageOut is None:
            self.pkgout = PackageOut()
        else:
            self.pkgout = pkgout
        self.filepath = str(filepath)
        self.testsrc = os.path.join(os.getcwd(),"src")
        self.testsuite = {}
        if not os.path.exists(self.filepath):
            self.pkgout.abort('File not found - ' + self.filepath)
        with open(self.filepath) as file:
            config = yaml.safe_load(file)
            if config is None:
                self.pkgout.abort('File is empty - ' + self.filepath)
        # read test name
        if "name" not in config:
            self.name = os.path.basename(self.filepath)
        else:
            self.name = config["name"]
        # set up esmf installation
        if "esmf" not in config:
            if os.environ.get('ESMFMKFILE') is None:
                self.pkgout.abort('[esmf] not found - ' + self.filepath)
            else:
                self.pkgout.warning('Using ESMFMKFILE environment variable')
                config["esmf"] = os.environ['ESMFMKFILE']
        self.esmf = ESMFInstallation(config["esmf"])
        # define directories
        self.builddir = os.path.abspath(os.path.join("build", self.esmf.vers,
                                                     self.esmf.mkdigest))
        self.testdir = os.path.abspath(os.path.join("run", self.name))
        self.logdir = os.path.abspath(os.path.join("logs", self.name))
        self.tcfgdir = os.path.abspath(os.path.join(self.builddir, "testcfg"))
        # read testsuite
        if "testsuite" not in config:
            self.pkgout.abort('[testsuite] not found - ' + self.filepath)
        elif config["testsuite"] is None:
            self.pkgout.abort('[testsuite] is empty - ' + self.filepath)
        else:
            for tname, opts in config["testsuite"].items():
                tname = tname.translate({ord(i): '_' for i in '/\\*'})
                if "repeat" in opts:
                    for i in range(opts["repeat"]):
                        newtname = tname + "-" + str(i + 1)
                        self.testsuite[newtname] = TestCase(newtname,
                            opts, self.testdir, self.pkgout)
                else:
                    self.testsuite[tname] = TestCase(tname,
                        opts, self.testdir, self.pkgout)
        # read profile
        self.profile = "SUMMARY"
        if "profile" in config:
            if isinstance(config["profile"], bool):
                if not config["profile"]:
                    self.profile = None
            else:
                self.profile = str(config["profile"]).upper()

    def run(self):
        self.rc = 0
        self.esmf.setenv()
        os.makedirs(self.builddir, exist_ok=True)
        os.makedirs(self.testdir, exist_ok=True)
        os.makedirs(self.tcfgdir, exist_ok=True)
        os.makedirs(self.logdir, exist_ok=True)
        for filename in os.listdir(self.tcfgdir):
            filepath = os.path.join(self.tcfgdir, filename)
            os.remove(filepath)
        logfpath = "{}/output-latest".format(self.logdir)
        resfpath = "{}/results-latest.xml".format(self.logdir)
        if os.path.exists(logfpath):
            ts = os.path.getmtime(logfpath)
            tsiso = dt.fromtimestamp(ts).replace(microsecond=0).isoformat()
            os.rename(logfpath, logfpath.replace("latest", tsiso))
        if os.path.exists(resfpath):
            ts = os.path.getmtime(resfpath)
            tsiso = dt.fromtimestamp(ts).replace(microsecond=0).isoformat()
            os.rename(resfpath, resfpath.replace("latest", tsiso))
        if self.profile is not None:
            os.environ["ESMF_RUNTIME_PROFILE"] = "ON"
            os.environ["ESMF_RUNTIME_PROFILE_OUTPUT"] = self.profile
        for tname in self.testsuite:
            self.testsuite[tname].write_cmake(self.tcfgdir)
            self.testsuite[tname].clean_tdir()
            self.testsuite[tname].setup_input()
        with open(logfpath, "w") as logf:
            logf.write(str(self.esmf))
            logf.flush()
            cp = subprocess.run(["cmake", self.testsrc],
                stdout=logf, stderr=logf, cwd=self.builddir)
            if cp.returncode != 0:
                self.pkgout.error('CMake failure detected, see ' +
                    str(logf.name)
                )
                self.rc = 101
            cp = subprocess.run(["make"],
                stdout=logf, stderr=logf, cwd=self.builddir)
            if cp.returncode != 0:
                self.pkgout.error('Make failure detected, see ' +
                    str(logf.name)
                )
                self.rc = 102
            cp = subprocess.run(["ctest", "--output-junit", resfpath],
                stdout=logf, stderr=logf, cwd=self.builddir)
            if cp.returncode != 0:
                self.pkgout.error('CTest failure detected, see ' +
                    str(logf.name)
                )
                self.rc = 103
        # read and print test results
        results = TestResults(resfpath, self.testsuite, self.esmf,
            self.pkgout
        )
        print(results)
        print("\nFINISHED: " + self.name + " (" + str(logf.name) + ")")
        return self.rc

def RunTestSuite(argv):

    # read input arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('testsuite', help='YAML configuration file')
    parser.add_argument('--color', help='add color to output',
        action='store_true'
    )
    args = parser.parse_args()

    p = PackageOut(args.color)
    t = TestSuite(args.testsuite, p)
    rc = t.run()
    return rc
