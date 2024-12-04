from pathlib import Path
import argparse
import os
import sys
import yaml
import subprocess
import datetime

class ESMFPerformanceTest():
    filepath: str = None
    config: dict = None
    esmfmkfile: str = None
    esmfconfig: dict = {}
    builddir: str = None
    logdir: str = None
    testsrc: str = os.path.join(os.getcwd(),"tests")

    def __init__(self, filepath: str):
        self.filepath = format(filepath)
        if not os.path.exists(self.filepath):
            self.error('File not found - ' + self.filepath)
        with open(self.filepath) as file:
            self.config = yaml.safe_load(file)
            if self.config is None:
                self.error('File is empty - ' + self.filepath)
        if "esmf" not in self.config:
            if os.environ.get('ESMFMKFILE') is None:
                self.error('[esmf] not found - ' + self.filepath)
            else:
                self.warning('Using ESMFMKFILE environment variable')
                self.esmfmkfile = os.environ['ESMFMKFILE']
        else:
            if os.path.basename(self.config["esmf"]) == 'esmf.mk':
                self.esmfmkfile = os.path.abspath(self.config["esmf"])
            else:
                for root, dirs, files in os.walk(self.config["esmf"]):
                    if 'esmf.mk' in files:
                        self.esmfmkfile = os.path.join(root, 'esmf.mk')
        if self.esmfmkfile is None:
            self.error('esmf.mk not found - ' + format(self.config["esmf"]))
        os.environ["ESMFMKFILE"] = self.esmfmkfile
        with open(self.esmfmkfile, "r") as file:
            for line in file:
                if line.lstrip().startswith('ESMF_'):
                    key, value = line.split("=", maxsplit=1)
                    self.esmfconfig[key] = value.rstrip()
        self.builddir = "build/" + os.path.basename(self.filepath)
        self.logdir = "logs/" + os.path.basename(self.filepath)

    def error(self, message: str):
        sys.exit('\033[91mERROR: ' + message + '\033[0m')

    def warning(self, message: str):
        print('\033[93mWARNING: ' + message + '\033[0m')

    def complete(self, message: str):
        print('\033[92mCOMPLETE: ' + message + '\033[0m')

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
        if os.path.exists(logfpath):
            ts = os.path.getmtime(logfpath)
            tsiso = datetime.datetime.fromtimestamp(ts).replace(microsecond=0).isoformat()
            os.rename(logfpath, logfpath.replace("latest", tsiso))
        with open(logfpath, "w") as logf:
            logf.write(self.esmf_vers_info())
            logf.flush()
            cp = subprocess.run(["cmake", self.testsrc],
                stdout=logf, stderr=logf, cwd=self.builddir)
            if cp.returncode != 0:
                self.error('CMake failure, see ' + format(logf.name))
            cp = subprocess.run(["make"],
                stdout=logf, stderr=logf, cwd=self.builddir)
            if cp.returncode != 0:
                self.error('Build failure, see ' + format(logf.name))
            cp = subprocess.run(["ctest"],
                stdout=logf, stderr=logf, cwd=self.builddir)
            if cp.returncode != 0:
                self.error('Test failure, see ' + format(logf.name))
        self.complete(self.filepath + ', see ' + format(logf.name))

def main(argv):

    # read input arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--ifile' , help='Input EPT file', required=True)
    args = parser.parse_args()

    ept = ESMFPerformanceTest(args.ifile)
    ept.execute_tests()

if __name__ == "__main__":
    main(sys.argv[1:])

