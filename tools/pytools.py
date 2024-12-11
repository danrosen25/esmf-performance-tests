#!/usr/bin/python3

from pathlib import Path
import argparse
import xml.etree.ElementTree as ET
import os
import sys
import yaml
import subprocess
import datetime

def error(message: str):
    print('\033[91mERROR: ' + message + '\033[0m')

def warning(message: str):
    print('\033[93mWARNING: ' + message + '\033[0m')

class TestResults():
    tests = []
    def __init__(self, filepath: str):
        self.append(filepath)
    def append(self, filepath: str):
        tree = ET.parse(filepath)
        root = tree.getroot()
        hostname = root.get('hostname')
        timestamp = root.get('timestamp')
        for t in root.findall('testcase'):
            self.tests.append({"name": t.get('name'),
                               "hostname": hostname,
                               "timestamp": timestamp,
                               "time": float(t.get('time')),
                               "status": t.get('status')})
    def __str__(self):
        res = (f"| " +
               f"{'name':20} | " +
               f"{'hostname':20} | " +
               f"{'status':6} | " +
               f"{'time (s)':9} |")
        res += ("\n| " +
                "-" * 20 + " | " +
                "-" * 20 + " | " +
                "-" * 6 + " | " +
                "-" * 9 + " |")
        for t in self.tests:
            res += (f"\n| " +
                   f"{t['name']:20} | " +
                   f"{t['hostname']:20} | " +
                   f"{t['status']:6} | " +
                   f"{t['time']:.3E} |")
        return res

class ESMFPerformanceTest():
    filepath: str = None
    config: dict = None
    esmfmkfile: str = None
    name: str = None
    esmfconfig: dict = {}
    builddir: str = None
    logdir: str = None
    testsrc: str = os.path.join(os.getcwd(),"tests")

    def __init__(self, filepath: str):
        self.filepath = format(filepath)
        if not os.path.exists(self.filepath):
            error('File not found - ' + self.filepath)
        with open(self.filepath) as file:
            self.config = yaml.safe_load(file)
            if self.config is None:
                error('File is empty - ' + self.filepath)
        if "name" not in self.config:
            self.name = os.path.basename(self.filepath)
        else:
            self.name = self.config["name"]
        if "esmf" not in self.config:
            if os.environ.get('ESMFMKFILE') is None:
                error('[esmf] not found - ' + self.filepath)
            else:
                warning('Using ESMFMKFILE environment variable')
                self.esmfmkfile = os.environ['ESMFMKFILE']
        else:
            if os.path.basename(self.config["esmf"]) == 'esmf.mk':
                self.esmfmkfile = os.path.abspath(self.config["esmf"])
            else:
                for root, dirs, files in os.walk(self.config["esmf"]):
                    if 'esmf.mk' in files:
                        self.esmfmkfile = os.path.join(root, 'esmf.mk')
        if self.esmfmkfile is None:
            error('esmf.mk not found - ' + format(self.config["esmf"]))
        os.environ["ESMFMKFILE"] = self.esmfmkfile
        with open(self.esmfmkfile, "r") as file:
            for line in file:
                if line.lstrip().startswith('ESMF_'):
                    key, value = line.split("=", maxsplit=1)
                    self.esmfconfig[key] = value.rstrip()
        self.builddir = os.path.abspath(os.path.join("build", self.name))
        self.logdir = os.path.abspath(os.path.join("logs", self.name))

    def esmf_vers_info(self):
        msg = ("ESMF Build Information" +
            "\n  Makefile Fragment: " + self.esmfmkfile +
            "\n  Version: " + self.esmfconfig["ESMF_VERSION_STRING"] +
            "\n  Git Version: " + self.esmfconfig["ESMF_VERSION_STRING_GIT"] +
            "\n  Public: " + self.esmfconfig["ESMF_VERSION_PUBLIC"] +
            "\n  Beta Snapshot: " + self.esmfconfig["ESMF_VERSION_BETASNAPSHOT"] +
            "\n")
        return msg

    def execute_tests(self):
        os.makedirs(self.builddir, exist_ok=True)
        os.makedirs(self.logdir, exist_ok=True)
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
        with open(logfpath, "w") as logf:
            logf.write(self.esmf_vers_info())
            logf.flush()
            cp = subprocess.run(["cmake", self.testsrc],
                stdout=logf, stderr=logf, cwd=self.builddir)
            if cp.returncode != 0:
                error('CMake failure, see ' + format(logf.name))
            cp = subprocess.run(["make"],
                stdout=logf, stderr=logf, cwd=self.builddir)
            if cp.returncode != 0:
                error('Build failure, see ' + format(logf.name))
            cp = subprocess.run(["ctest", "--output-junit", resfpath],
                stdout=logf, stderr=logf, cwd=self.builddir)
            if cp.returncode != 0:
                error('Test failure, see ' + format(logf.name))
        results = TestResults(resfpath)
        print("FINISHED: " + self.name + " (" + format(logf.name) + ")")
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

