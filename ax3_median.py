#!/usr/bin/env python3
# coding=UTF-8
#
# BSD 2-Clause License
#
# Copyright (c) 2020, Jason Leake
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
# Median filter for AX3 CSV data
#

# Axes:
# X is the long axis
# Y is the across-the-device axis
# Z is across the thickness of the device axis
from Row import Row
from tkinter import filedialog
import argparse
import csv
import math
import numpy as np
import os
import sys
import tkinter as tk
from medianfilter import medianFilter

class MedianProcessor:
    
    def makeOutFile(self, filename):
        """ Make output filename """
        path, name = os.path.split(filename)
        newName = "median_" + name
        fullPath = os.path.join(path, newName)
        print("Output file is", fullPath)
        return fullPath

    def process(self, filename, window):
        """ Process the file """
        # Count number of lines in file to get array dimension
        print("Count lines in file")
        count = 0
        with open(filename, "rt", newline="\n") as fh:
            line = fh.readline().strip()
            while line:
                row = Row(line)
                if row.skip:
                    pass
                else:
                    count += 1
                if count % 1000000 == 0:
                    print(f"{count} lines counted")
                line = fh.readline().strip()

        # Set initial values of array to match actual field length
        timestamp = np.array(["YYYY-MM-DD HH:MM:SS.FFF" for _ in range(count)])
        x = np.zeros((count,))
        y = np.zeros((count,))
        z = np.zeros((count,))

        print("Read file")
        firstLine = None
        with open(filename, "rt", newline="\n") as fh:
            line = fh.readline().strip()
            index = 0
            while line:
                row = Row(line)
                if row.skip:
                     pass
                else:
                    if firstLine is None:
                         firstLine = row.timestamp
                    timestamp[index] = row.timestamp
                    x[index] = row.val[0]
                    y[index] = row.val[1]
                    z[index] = row.val[2]
                    index += 1
                if index % 1000000 == 0:
                    print(f"{index} data lines read")

                line = fh.readline().strip()

        print("Calculate x axis medians")
        medx = medianFilter(x, window, len(x)//50)
        print("Calculate y axis medians")
        medy = medianFilter(y, window, len(y)//50)
        print("Calculate z axis medians")
        medz = medianFilter(z, window, len(z)//50)

        outputFilename = self.makeOutFile(filename)
        lineEnd = "\r\n"
        with open(outputFilename, "w") as outfile:
            outfile.write("datetime, x, y, z{}".format(lineEnd))
            for index in range(len(timestamp)):
                outfile.write("{},{:.06f},{:.06f},{:.06f}{}".format(
                    timestamp[index], medx[index],
                    medy[index], medz[index], lineEnd))
        return outputFilename

def main():
    if len(sys.argv) < 2:
        root = tk.Tk()
        root.withdraw()
        filePath = filedialog.askopenfilename(
            filetypes = [("Comma separated file (CSV) format",".csv")])
        window = 7
    else:
        parser = argparse.ArgumentParser(description=
                                         "Convert accelerometer file to per second values")
        parser.add_argument("filename", help="Input filename")
        parser.add_argument("--window", help="Window size",
                            type=int, default="7")
        args = parser.parse_args()
        filePath = args.filename
        name, extension =  os.path.splitext(filePath)
        window = args.window

        if window < 0:
            print(f"Bad value for window, {window}, using 25")
            window = 25
        if window % 2 != 1:
            print(f"Window size must be odd, {window}, using 25")
            window = 25
            
        if extension == ".CWA":
            print("You need the .csv, not the .CWA", file=stderr)
            os.exit(0)

    processor = MedianProcessor()
    processor.process(filePath, window)

if __name__ == "__main__":
    main()

