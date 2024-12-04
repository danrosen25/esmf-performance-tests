from pathlib import Path
import argparse
import os
import sys
import yaml
import subprocess

class ESMFPerformanceTest():
    config: dict = None
    esmfmkfile: str = None
    esmfconfig: dict = {}

    def __init__(self, file_path):
        if not os.path.exists(file_path):
            sys.exit('File not found: {}'.format(file_path))
        with open(file_path) as file:
            data = yaml.safe_load(file)
            if data is None:
                sys.exit('File is empty: {}'.format(file_path))
            else:
                self.config = dict({k.replace("-", "_"): v for k, v in data.items()})
        if "esmf" not in self.config:
            if os.environ.get('ESMFMKFILE') is None:
                sys.exit('[esmf] not found: {}'.format(file_path))
            else:
                print("\033[93mWARNING: Using ESMFMKFILE environment variable\033[0m")
                self.esmfmkfile = os.environ['ESMFMKFILE']
        else:
            for root, dirs, files in os.walk(self.config["esmf"]):
                if 'esmf.mk' in files:
                    self.esmfmkfile = os.path.join(root, 'esmf.mk')
        os.environ["ESMFMKFILE"] = self.esmfmkfile
        if self.esmfmkfile is None:
            sys.exit('esmf.mk not found: {}'.format(self.config["esmf"]))
        with open(self.esmfmkfile, "r") as file:
            for line in file:
                if line.lstrip().startswith('ESMF_'):
                    key, value = line.split("=", maxsplit=1)
                    self.esmfconfig[key] = value.rstrip()

    def print_esmf_vers(self):
        print("ESMF Build Information")
        print("  Makefile Fragment: {}".format(self.esmfmkfile))
        print("  Version: {}".format(self.esmfconfig["ESMF_VERSION_STRING"]))
        print("  Git Version: {}".format(self.esmfconfig["ESMF_VERSION_STRING_GIT"]))
        print("  Public: {}".format(self.esmfconfig["ESMF_VERSION_PUBLIC"]))
        print("  Beta Snapshot: {}".format(self.esmfconfig["ESMF_VERSION_BETASNAPSHOT"]))

def main(argv):

    # read input arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--ifile' , help='Input EPT file', required=True)
    args = parser.parse_args()

    # read app configuration yaml file
    ept = ESMFPerformanceTest(args.ifile)
    ept.print_esmf_vers()

    if not os.path.exists("build"):
        os.mkdir("build")
    subprocess.call(["cmake", "../tests"], cwd="build")
    subprocess.call(["make"], cwd="build")
    subprocess.call(["ctest"], cwd="build")

if __name__ == "__main__":
    main(sys.argv[1:])

