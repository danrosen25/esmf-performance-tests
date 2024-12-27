#!/usr/bin/python3

from pathlib import Path
import argparse
import xml.etree.ElementTree as ET
import os
import sys
import yaml
import subprocess
import datetime
import hashlib

def abort(message: str):
    sys.exit('\033[91mERROR: ' + message + '\033[0m')

def error(message: str):
    print('\033[91mERROR: ' + message + '\033[0m')

def warning(message: str):
    print('\033[93mWARNING: ' + message + '\033[0m')

class ESMFInstallation():
    mkfile: str = None
    mkdigest: str = None
    config: dict = {}
    vers: str = None

    def __init__(self, esmfpath: str):
        if os.path.basename(esmfpath) == 'esmf.mk':
            self.mkfile = os.path.abspath(esmfpath)
            if not os.path.exists(self.mkfile):
                abort('esmf.mk file not found - ' + esmfpath)
        else:
            for root, dirs, files in os.walk(esmfpath):
                if 'esmf.mk' in files:
                    self.mkfile = os.path.join(root, 'esmf.mk')
                    break
            if self.mkfile is None:
                abort('esmf.mk file not found - ' + esmfpath)
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

class TestCase():
    name: str = None
    cmakef: str = None
    tdir: str = None
    options: dict = {}
    executable: str = None
    mpi: bool = True
    mpinp: str = "1"
    timeout: int = 0
    arguments: str = None
    inputdata: str = None

    def __init__(self, name: str, options: dict, rundir: str):
        self.name = name
        self.cmakef = self.name + ".cmake"
        self.tdir = os.path.abspath(os.path.join(rundir, self.name))
        if options is None:
            abort('test options missing - ' + self.name)
        if "executable" not in options:
            abort('[executable] missing - ' + self.name)
        else:
            self.executable = str(options["executable"])
        if "mpi" in options:
            self.mpi = bool(options["mpi"])
        if self.mpi:
            if "mpinp" in options:
                self.mpinp = str(options["mpinp"])
        else:
            self.mpinp = "N/A"
        if "timeout" in options:
            self.timeout = int(options["timeout"])
        if "arguments" in options:
            self.arguments = str(options["arguments"])
        if "inputdata" in options:
            self.inputdata = str(options["inputdata"])

    def write_cmake(self, tcfgdir: str):
        # generate <test>.cmake file
        output = '# name: ' + self.name + '\n\n'
        output += 'list(APPEND TESTLIST ' + self.name + ')\n'
        output += 'file(REMOVE_RECURSE "' + self.tdir + '")\n'
        output += 'file(MAKE_DIRECTORY "' + self.tdir + '")\n'
        if self.inputdata is not None:
            inputdata = os.path.abspath(self.inputdata)
            output += ('file(COPY "' + inputdata + '"\n' +
                      '\tDESTINATION "' + self.tdir + '")\n')
        if self.mpi:
            output += 'if(NOT MPI_Fortran_FOUND)\n'
            output += '\tMESSAGE(ERROR "' + self.name + ' requires MPI")\n'
            output += 'endif()\n'
            output += 'add_test(NAME ' + self.name + ' COMMAND\n'
            output += ('\t${MPIEXEC}' +
                       ' ${MPIEXEC_NUMPROC_FLAG} ' + self.mpinp +
                       ' $<TARGET_FILE:' + self.executable + '>\n')
        else:
            output += 'add_test(NAME ' + self.name + ' COMMAND\n'
            output += '\t$<TARGET_FILE:' + self.executable + '>\n'
        if self.arguments is not None:
            output += '\t' + self.arguments + '\n'
        output += '\tWORKING_DIRECTORY ' + self.tdir + ')\n'
        output += ('set_tests_properties(' + self.name + ' PROPERTIES' +
                   ' TIMEOUT ' + str(self.timeout) + ')\n')
        fpath = os.path.abspath(os.path.join(tcfgdir, self.cmakef))
        with open(fpath, "w") as cmakef:
            cmakef.write(output)

    def __str__(self):
        return self.name

class TestResults():
    tests = []
    def __init__(self, resfile: str, testsuite: dict, esmf: ESMFInstallation):
        self.append(resfile, testsuite, esmf)
    def append(self, resfile: str, testsuite: dict, esmf: ESMFInstallation):
        tree = ET.parse(resfile)
        root = tree.getroot()
        hostname = root.get('hostname')
        timestamp = root.get('timestamp')
        for t in root.findall('testcase'):
            testname = t.get('name')
            self.tests.append({"name": testname,
                               "hostname": hostname,
                               "esmfvers": esmf.vers,
                               "timestamp": timestamp,
                               "mpi": testsuite[testname].mpi,
                               "mpinp": testsuite[testname].mpinp,
                               "status": t.get('status'),
                               "time": float(t.get('time'))})
    def __str__(self):
        res = (f"| " +
               f"{'name':30} | " +
               f"{'hostname':12} | " +
               f"{'esmf':10} | " +
               f"{'mpi':5} | " +
               f"{'mpinp':6} | " +
               f"{'status':6} | " +
               f"{'time (s)':9} |")
        res += ("\n| " +
                "-" * 30 + " | " +
                "-" * 12 + " | " +
                "-" * 10 + " | " +
                "-" * 5 + " | " +
                "-" * 6 + " | " +
                "-" * 6 + " | " +
                "-" * 9 + " |")
        for t in self.tests:
            res += (f"\n| " +
                   f"{t['name']:30} | " +
                   f"{t['hostname']:12} | " +
                   f"{t['esmfvers']:10} | " +
                   f"{t['mpi']:5} | " +
                   f"{t['mpinp']:6} | " +
                   f"{t['status']:6} | " +
                   f"{t['time']:.3E} |")
        return res

class ESMFPerformanceTest():
    filepath: str = None
    name: str = None
    esmf: ESMFInstallation = None
    profile: bool = False
    builddir: str = None
    testdir: str = None
    logdir: str = None
    testsrc: str = os.path.join(os.getcwd(),"src")
    testsuite: TestCase = {}

    def __init__(self, filepath: str):
        self.filepath = str(filepath)
        if not os.path.exists(self.filepath):
            abort('File not found - ' + self.filepath)
        with open(self.filepath) as file:
            config = yaml.safe_load(file)
            if config is None:
                abort('File is empty - ' + self.filepath)
        # read test name
        if "name" not in config:
            self.name = os.path.basename(self.filepath)
        else:
            self.name = config["name"]
        # set up esmf installation
        if "esmf" not in config:
            if os.environ.get('ESMFMKFILE') is None:
                abort('[esmf] not found - ' + self.filepath)
            else:
                warning('Using ESMFMKFILE environment variable')
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
            abort('[testsuite] not found - ' + self.filepath)
        elif config["testsuite"] is None:
            abort('[testsuite] is empty - ' + self.filepath)
        else:
            for tname, opts in config["testsuite"].items():
                if "repeat" in opts:
                    for i in range(opts["repeat"]):
                        newtname = tname + "-" + str(i + 1)
                        self.testsuite[newtname] = TestCase(newtname,
                            opts, self.testdir)
                else:
                    self.testsuite[tname] = TestCase(tname,
                        opts, self.testdir)
        # read profile
        if "profile" in config:
            self.profile = config["profile"]

    def execute_tests(self):
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
            tsiso = datetime.datetime.fromtimestamp(ts).replace(microsecond=0).isoformat()
            os.rename(logfpath, logfpath.replace("latest", tsiso))
        if os.path.exists(resfpath):
            ts = os.path.getmtime(resfpath)
            tsiso = datetime.datetime.fromtimestamp(ts).replace(microsecond=0).isoformat()
            os.rename(resfpath, resfpath.replace("latest", tsiso))
        if self.profile:
            os.environ["ESMF_RUNTIME_PROFILE"] = "ON"
            os.environ["ESMF_RUNTIME_PROFILE_OUTPUT"] = "SUMMARY"
        for tname in self.testsuite:
            self.testsuite[tname].write_cmake(self.tcfgdir)
        with open(logfpath, "w") as logf:
            logf.write(str(self.esmf))
            logf.flush()
            cp = subprocess.run(["cmake", self.testsrc],
                stdout=logf, stderr=logf, cwd=self.builddir)
            if cp.returncode != 0:
                error('CMake failure, see ' + str(logf.name))
            cp = subprocess.run(["make"],
                stdout=logf, stderr=logf, cwd=self.builddir)
            if cp.returncode != 0:
                error('Build failure, see ' + str(logf.name))
            cp = subprocess.run(["ctest", "--output-junit", resfpath],
                stdout=logf, stderr=logf, cwd=self.builddir)
            if cp.returncode != 0:
                error('Test failure, see ' + str(logf.name))
        print("FINISHED: " + self.name + " (" + str(logf.name) + ")")
        # read and print test results
        results = TestResults(resfpath, self.testsuite, self.esmf)
        print(results)

def main(argv):

    # read input arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--ifile' , help='Input EPT file', required=True)
    args = parser.parse_args()

    ept = ESMFPerformanceTest(args.ifile)
    ept.execute_tests()

if __name__ == "__main__":
    main(sys.argv[1:])

