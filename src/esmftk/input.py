# -*- coding: utf-8 -*-
'''
ESMF TestKit (esmftk)

Copyright (c) 2002-2025 University Corporation for Atmospheric Research,
Massachusetts Institute of Technology, Geophysical Fluid Dynamics Laboratory,
University of Michigan, National Centers for Environmental Prediction, Los
Alamos National Laboratory, Argonne National Laboratory, NASA Goddard Space
Flight Center. All rights reserved.
'''

#standard
from datetime import datetime as dt
from getpass import getuser
from importlib.resources import files
import os
import re
import shutil
# local
from .packageout import *

class Input():

    def __init__(self, settings: dict, pkgout: PackageOut=None):
        if PackageOut is None:
            self.pkgout = PackageOut()
        else:
            self.pkgout = pkgout
        if 'type' in settings:
            self.itype = settings['type']
        else:
            self.itype = 'copy'
        if self.itype not in ['copy', 'template']:
            self.pkgout.abort("invalid inputdata type - " + self.itype)
        if 'infile' not in settings:
            self.pkgout.abort('inputdata requires infile')
        else:
            self.infile = str(settings['infile'])
        if os.path.exists(self.infile):
            pass
        elif os.path.exists(os.path.join(files(__package__), self.infile)):
            self.infile = os.path.join(files(__package__), self.infile)
        else:
            self.pkgout.abort("input - infile not found " + self.infile)
        if 'outfile' not in settings:
            self.outfile = os.path.basename(self.infile)
        else:
            self.outfile = str(settings['outfile'])
        if 'vars' in settings:
            self.vardict = settings['vars']
        else:
            self.vardict = {}

    @classmethod
    def from_string(cls, fpath: str, pkgout: PackageOut=None):
        return cls({'type': 'copy', 'infile': fpath}, pkgout)

    def setup(self, outdir: str):
        if self.itype == 'copy':
            self.copy_file(outdir)
        elif self.itype == 'template':
            self.fill_template(outdir)
        else:
            self.pkgout.abort("unknown input type " + self.itype)

    def copy_file(self, outdir: str):
        if os.path.isfile(self.infile):
            shutil.copy(self.infile, os.path.join(outdir, self.outfile))
        elif os.path.isdir(self.infile):
            shutil.copytree(self.infile, os.path.join(outdir, self.outfile))
        else:
            self.pkgout.abort("copy - missing file " + self.infile)

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
                        self.pkgout.abortfp("var - missing name",
                            self.infile, index
                        )
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
                        self.pkgout.abortfp("var - missing value",
                            self.infile, index
                        )
                elif typ == 'env':
                    if len(line) == 0:
                        self.pkgout.abortfp("env - missing name",
                            self.infile, index
                        )
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
                        self.pkgout.abortfp("env - missing value",
                            self.infile, index
                        )
                elif typ == 'username':
                    ofile.write(getuser())
                elif typ == 'template':
                    ofile.write(os.path.abspath(self.infile))
                elif typ == 'date':
                    if len(line) == 0:
                        ofile.write(dt.now().strftime("%Y-%m-%d"))
                    else:
                        ofile.write(dt.now().strftime(line))
                else:
                    self.pkgout.abortfp(typ + " - unknown type",
                        self.infile, index
                    )
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
