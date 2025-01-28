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
import xml.etree.ElementTree as ET
# local
from .esmfinstall import *
from .packageout import *

class CsvStr(str):
    def __new__(cls, content):
        if any(c in content for c in [' ', ',', '"', '\n']):
            return super(CsvStr, cls).__new__(
                cls, '"' + content.replace('"', '""') + '"')
        else:
            return super(CsvStr, cls).__new__(cls, content)

class TestResults():

    def __init__(self, resfile: str, testsuite: dict, esmf: ESMFInstallation,
            pkgout: PackageOut=None):
        if PackageOut is None:
            self.pkgout = PackageOut()
        else:
            self.pkgout = pkgout
        self.tests = []
        self.append(resfile, testsuite, esmf)

    def append(self, resfile: str, testsuite: dict, esmf: ESMFInstallation):
        tree = ET.parse(resfile)
        root = tree.getroot()
        hostname = root.get('hostname')
        timestamp = root.get('timestamp')
        for tname, tcase in testsuite.items():
            tres = root.find(".//testcase[@name='" + tname + "']")
            self.tests.append({"name": tres.get('name'),
                               "hostname": hostname,
                               "esmfvers": esmf.vers,
                               "timestamp": timestamp,
                               "mpi": str(tcase.mpi)[0],
                               "mpinp": tcase.mpinp,
                               "status": tres.get('status'),
                               "time": float(tres.get('time'))})

    def csv(self):
        res = (f"name," +
               f"hostname," +
               f"esmf," +
               f"mpi," +
               f"mpinp," +
               f"status," +
               f"time_s")
        for t in self.tests:
            res += (f"\n" +
                    CsvStr(f"{t['name']}") + "," +
                    CsvStr(f"{t['hostname']}") + "," +
                    CsvStr(f"{t['esmfvers']}") + "," +
                    CsvStr(f"{t['mpi']}") + "," +
                    CsvStr(f"{t['mpinp']}") + "," +
                    CsvStr(f"{t['status']}") + "," +
                    CsvStr(f"{t['time']:.3E}"))
        return res

    def markdown(self):
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

    def __str__(self):
        return self.markdown()
