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
import os
import shutil
# local
from .input import *
from .packageout import *

class TestCase():

    def __init__(self, name: str, options: dict, rundir: str,
            pkgout: PackageOut=None):
        if PackageOut is None:
            self.pkgout = PackageOut()
        else:
            self.pkgout = pkgout
        self.name = name
        self.cmakef = self.name + ".cmake"
        self.tdir = os.path.abspath(os.path.join(rundir, self.name))
        if options is None:
            self.pkgout.abort('test options missing - ' + self.name)
        if "executable" not in options:
            self.pkgout.abort('[executable] missing - ' + self.name)
        else:
            self.exe = os.path.basename(options["executable"])
            self.exedir = os.path.abspath(
                os.path.dirname(options["executable"])
            )
        if "mpi" in options:
            self.mpi = bool(options["mpi"])
        else:
            self.mpi = True
        if self.mpi:
            if "mpinp" in options:
                self.mpinp = str(options["mpinp"])
            else:
                self.mpinp = "1"
        else:
            self.mpinp = "N/A"
        if "timeout" in options:
            self.timeout = float(options["timeout"])
        else:
            self.timeout = 0
        if "arguments" in options:
            self.arguments = str(options["arguments"])
        else:
            self.arguments = None
        self.inputdata = []
        if "inputdata" in options:
            if isinstance(options["inputdata"], list):
                for inputitem in options["inputdata"]:
                    if isinstance(inputitem, dict):
                        self.inputdata.append(
                            Input(inputitem, self.pkgout)
                        )
                    elif isinstance(inputitem, str):
                        self.inputdata.append(
                            Input.from_string(inputitem, self.pkgout)
                        )
                    else:
                        self.pkgout.abort(
                            "inputdata format not supported - " + self.name
                        )
            elif isinstance(options["inputdata"], dict):
                self.inputdata.append(
                    Input(options["inputdata"], self.pkgout)
                )
            elif isinstance(options["inputdata"], str):
                self.inputdata.append(
                    Input.from_string(options["inputdata"], self.pkgout)
                )
            else:
                self.pkgout.abort(
                    "inputdata format not supported - " + self.name
                )

    def write_cmake(self, tcfgdir: str):
        # generate <test>.cmake file
        output = '# name: ' + self.name + '\n\n'
        output += 'list(APPEND TESTLIST ' + self.name + ')\n'
        output += 'if(TARGET ' + self.exe + ')\n'
        output += '\tset(TEST_EXE $<TARGET_FILE:' + self.exe + '>)\n'
        output += 'else()\n'
        output += ('\tfind_program(TEST_EXE ' + self.exe +
                   ' PATHS "' + self.exedir + '" NO_CACHE)\n')
        output += 'endif()\n'
        output += 'if(NOT TEST_EXE)\n'
        output += ('\tMESSAGE(FATAL_ERROR "executable not found: ' +
                   os.path.join(self.exedir, self.exe) + '")\n')
        output += 'endif()\n'
        if self.mpi:
            output += 'if(NOT MPI_FOUND)\n'
            output += ('\tMESSAGE(FATAL_ERROR "' + self.name +
                       ' requires MPI")\n')
            output += 'endif()\n'
            output += 'add_test(NAME ' + self.name + ' COMMAND\n'
            output += ('\t${MPIEXEC}' +
                       ' ${MPIEXEC_NUMPROC_FLAG} ' + self.mpinp +
                       ' ${TEST_EXE}\n')
        else:
            output += 'add_test(NAME ' + self.name + ' COMMAND\n'
            output += '\t${TEST_EXE}\n'
        if self.arguments is not None:
            output += '\t' + self.arguments + '\n'
        output += '\tWORKING_DIRECTORY ' + self.tdir + ')\n'
        output += ('set_tests_properties(' + self.name + ' PROPERTIES' +
                   ' TIMEOUT ' + str(self.timeout) + ')\n')
        output += 'unset(TEST_EXE)\n'
        fpath = os.path.abspath(os.path.join(tcfgdir, self.cmakef))
        with open(fpath, "w") as cmakef:
            cmakef.write(output)

    def clean_tdir(self):
        if os.path.exists(self.tdir):
            shutil.rmtree(self.tdir)
        os.makedirs(self.tdir, exist_ok=True)

    def setup_input(self):
        for inputitem in self.inputdata:
            inputitem.setup(self.tdir)

    def __str__(self):
        return self.name
