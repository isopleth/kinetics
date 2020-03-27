#!/usr/bin/env python3
# coding=UTF-8
#
# BSD 2-Clause License
#
# Copyright (c) 2019, Jason Leake
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Split SX3 CSV file into per-day files
#

# Axes:
# X is the long axis
# Y is the across-the-device axis
# Z is the across-the-device axis
import numpy as np
import argparse
import sys
from tkinter import filedialog
import tkinter as tk
import csv
from Row import Row
import os

class Processor:

    def makeOutFile(self, filename, date):
        """ Make output filename """
        path, name = os.path.split(filename)
        prefix = os.path.splitext(name)[0]
        newName = prefix + "_" + date + ".csv"
        fullPath = os.path.join(path, newName)
        print("Output file is", fullPath)
        return fullPath

    def __call__(self, filename):
        """ Split the CSV file into per-day files """
        outfiles = []
        date = None
        outfile = None
        with open(filename, "rt", newline="\n") as self.fh:
            line = self.fh.readline().strip()
            while line:
                row = Row(line, True, False)
                if row.skip:
                    pass
                else:
                    if row.date != date:
                        date = row.date
                        outputFilename = self.makeOutFile(filename, date)
                        outfiles.append(outputFilename)
                        if outfile is not None:
                            outfile.close()
                        outfile = open(outputFilename, "w")
                    outfile.write(row.rawLine + "\n")
                line = self.fh.readline().strip()
        if outfile is not None:
            outfile.close()
        return outfiles

def split(filePath):
    processor = Processor()
    return processor(filePath)

def main():
    if len(sys.argv) < 2:
        root = tk.Tk()
        root.withdraw()
        filePath = filedialog.askopenfilename(
            filetypes = [("Comma separated file (CSV) format",".csv")])
    else:
        parser = argparse.ArgumentParser(description=
                                         "Split accelerometer CSV file into per day files")
        parser.add_argument("filename", help="Input filename")
        args = parser.parse_args()
        filePath = args.filename
        name, extension =  os.path.splitext(filePath)

        if extension == ".CWA":
            print("You need the .csv, not the .CWA", file=stderr)
            os.exit(0)

    split(filePath)

if __name__ == "__main__":
    main()

