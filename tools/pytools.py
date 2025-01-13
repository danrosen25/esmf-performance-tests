#!/usr/bin/python3

from pathlib import Path
import argparse
import xml.etree.ElementTree as ET
import os
import sys
import yaml
import subprocess
from datetime import datetime as dt
import hashlib
import shutil
import re

def abort(message: str):
    sys.exit('\033[91mERROR: ' + message + '\033[0m')

def abortf(message: str, fpath: str, pos: int):
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
    sys.exit('\033[91mERROR: ' + message + ' (' +
        fpath + ':' + str(lcount) + ':' + str(ccount) + ')' +
        '\033[0m'
    )

def error(message: str):
    print('\033[91mERROR: ' + message + '\033[0m')

def warning(message: str):
    print('\033[93mWARNING: ' + message + '\033[0m')

class ESMFInstallation():

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

class Input():

    def __init__(self, settings: dict):
        if 'type' in settings:
            self.itype = settings['type']
        else:
            self.itype = 'copy'
        if self.itype not in ['copy', 'template']:
            abort("invalid inputdata type - " + self.itype)
        if 'infile' not in settings:
            abort('inputdata requires infile')
        else:
            self.infile = str(settings['infile'])
        if 'outfile' not in settings:
            self.outfile = os.path.basename(self.infile)
        else:
            self.outfile = str(settings['outfile'])
        if 'vars' in settings:
            self.vardict = settings['vars']
        else:
            self.vardict = {}

    @classmethod
    def from_string(cls, fpath: str):
        return cls({'type': 'copy', 'infile': fpath})

    def setup(self, outdir: str):
        if self.itype == 'copy':
            self.copy_file(outdir)
        elif self.itype == 'template':
            self.fill_template(outdir)

    def copy_file(self, outdir: str):
        if os.path.isfile(self.infile):
            shutil.copy(self.infile, os.path.join(outdir, self.outfile))
        elif os.path.isdir(self.infile):
            shutil.copytree(self.infile, os.path.join(outdir, self.outfile))

    def fill_template(self, outdir: str):
        tpattern = re.compile(
            r"(?<!\\)\{@\s+" +
            r"(?P<type>[^\s]*)\s+" +
            r"(?P<line>.*?)\s*" +
            r"(?<!\\)@\}"
        )
        dpattern = re.compile(
            r"(?<!\\):-"
        )
        with open(self.infile, "r") as tfile:
            template = tfile.read()
        with open(os.path.join(outdir, self.outfile), 'w') as ofile:
            index = 0
            eof = len(template)
            match = tpattern.search(template, index)
            while match is not None:
                if match.start() > index:
                    ofile.write(template[index:match.start()])
                index = match.start()
                typ = match.group("type")
                line = match.group("line")
                if typ == 'var':
                    if len(line) == 0:
                        abortf("var - missing name", self.infile, index)
                    elif dpattern.search(line):
                        var, dflt = dpattern.split(line, maxsplit=1)
                    else:
                        var = line
                        dflt = None
                    if var in self.vardict:
                        ofile.write(str(self.vardict[var]))
                    elif dflt is not None:
                        ofile.write(str(dflt))
                    else:
                        abortf("var - missing value", self.infile, index)
                elif typ == 'env':
                    if len(line) == 0:
                        abortf("env - missing name", self.infile, index)
                    elif dpattern.search(line):
                        var, dflt = dpattern.split(line, maxsplit=1)
                    else:
                        var = line
                        dflt = None
                    if var in os.environ:
                        ofile.write(os.environ[var])
                    elif dflt is not None:
                        ofile.write(str(dflt))
                    else:
                        abortf("env - missing value", self.infile, index)
                elif typ == 'username':
                    ofile.write(os.getlogin())
                elif typ == 'template':
                    ofile.write(os.path.abspath(self.infile))
                elif typ == 'date':
                    if len(line) == 0:
                        ofile.write(dt.now().strftime("%Y-%m-%d"))
                    else:
                        ofile.write(dt.now().strftime(line))
                else:
                    abortf(typ + " - unknown type", self.infile, index)
                index = match.end()
                match = tpattern.search(template, index)
            if eof > index:
                ofile.write(template[index:eof])

    def __str__(self):
        msg = ("Input Information" +
            "\n  type: " + self.itype +
            "\n  infile: " + self.infile +
            "\n  outfile: " + self.outfile +
            "\n")
        return msg

class TestCase():

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
            self.timeout = int(options["timeout"])
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
                        self.inputdata.append(Input(inputitem))
                    elif isinstance(inputitem, str):
                        self.inputdata.append(Input.from_string(inputitem))
                    else:
                        abort("inputdata format not supported - " + self.name)
            elif isinstance(options["inputdata"], dict):
                self.inputdata.append(Input(options["inputdata"]))
            elif isinstance(options["inputdata"], str):
                self.inputdata.append(Input.from_string(options["inputdata"]))
            else:
                abort("inputdata format not supported - " + self.name)

    def write_cmake(self, tcfgdir: str):
        # generate <test>.cmake file
        output = '# name: ' + self.name + '\n\n'
        output += 'list(APPEND TESTLIST ' + self.name + ')\n'
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

    def clean_tdir(self):
        if os.path.exists(self.tdir):
            shutil.rmtree(self.tdir)
        os.makedirs(self.tdir, exist_ok=True)

    def setup_input(self):
        for inputitem in self.inputdata:
            inputitem.setup(self.tdir)

    def __str__(self):
        return self.name

class TestResults():

    def __init__(self, resfile: str, testsuite: dict, esmf: ESMFInstallation):
        self.tests = []
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
                               "mpi": str(testsuite[testname].mpi)[0],
                               "mpinp": testsuite[testname].mpinp,
                               "status": t.get('status'),
                               "time": float(t.get('time'))})
    def __str__(self):
        wd = [ len('name'),
               len('hostname'),
               len('esmf'),
               len('mpinp')]
        for t in self.tests:
            wd[0] = max(wd[0], len(f"{t['name']}"))
            wd[1] = max(wd[1], len(f"{t['hostname']}"))
            wd[2] = max(wd[2], len(f"{t['esmfvers']}"))
            wd[3] = max(wd[3], len(f"{t['mpinp']}"))
        res = (f"| " +
               f"{'name':{wd[0]}} | " +
               f"{'hostname':{wd[1]}} | " +
               f"{'esmf':{wd[2]}} | " +
               f"{'mpi':3} | " +
               f"{'mpinp':{wd[3]}} | " +
               f"{'status':6} | " +
               f"{'time (s)':9} |")
        res += ("\n| " +
                "-" * wd[0] + " | " +
                "-" * wd[1] + " | " +
                "-" * wd[2] + " | " +
                "-" * 3 + " | " +
                "-" * wd[3] + " | " +
                "-" * 6 + " | " +
                "-" * 9 + " |")
        for t in self.tests:
            res += (f"\n| " +
                   f"{t['name']:{wd[0]}} | " +
                   f"{t['hostname']:{wd[1]}} | " +
                   f"{t['esmfvers']:{wd[2]}} | " +
                   f"{t['mpi']:3} | " +
                   f"{t['mpinp']:{wd[3]}} | " +
                   f"{t['status']:6} | " +
                   f"{t['time']:.3E} |")
        return res

class ESMFPerformanceTest():

    def __init__(self, filepath: str):
        self.filepath = str(filepath)
        self.testsrc = os.path.join(os.getcwd(),"src")
        self.testsuite = {}
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
                tname = tname.translate({ord(i): '_' for i in '/\\*'})
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
        else:
            self.profile = False

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
            tsiso = dt.fromtimestamp(ts).replace(microsecond=0).isoformat()
            os.rename(logfpath, logfpath.replace("latest", tsiso))
        if os.path.exists(resfpath):
            ts = os.path.getmtime(resfpath)
            tsiso = dt.fromtimestamp(ts).replace(microsecond=0).isoformat()
            os.rename(resfpath, resfpath.replace("latest", tsiso))
        if self.profile:
            os.environ["ESMF_RUNTIME_PROFILE"] = "ON"
            os.environ["ESMF_RUNTIME_PROFILE_OUTPUT"] = "SUMMARY"
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
    if sys.version_info < (3, 9):
        raise Exception("Python 3.9 or higher is required.")
    main(sys.argv[1:])

