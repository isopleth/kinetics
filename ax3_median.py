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
# Generate per-second accelerometer data
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

class MedianProcessor:

    def medianFilter(self, inputArray, window):
        """Apply median filter to an array.  Based on
        https://gist.github.com/bhawkins/3535131 """
        assert window % 2 == 1, "Median filter length must be odd."
        halfWindow = (window - 1) // 2
        # Create an array containing the window-full of points for each
        # point in the input array.  Once this is filled, use the
        # numpy median() to calculate the median of each
        outputArray = np.zeros((len(inputArray), window),
                               dtype=inputArray.dtype)
        # Filling in each point in the centre of the window
        outputArray[:,halfWindow] = inputArray
        # Now fill in the rest of the windows
        for windowIndex in range(halfWindow):
            halfWindowIndex = halfWindow - windowIndex
            outputArray[:halfWindowIndex, windowIndex] = inputArray[0]
            outputArray[-halfWindowIndex:, -(windowIndex + 1)] = inputArray[-1]
            outputArray[halfWindowIndex:, windowIndex] = inputArray[:-halfWindowIndex]            
            outputArray[:-halfWindowIndex, -(windowIndex + 1)] = inputArray[halfWindowIndex:]
            
        return np.median(outputArray, axis=1)
        
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
        medx = self.medianFilter(x, window)
        medy = self.medianFilter(y, window)
        medz = self.medianFilter(z, window)

        outputFilename = self.makeOutFile(filename)
        with open(outputFilename, "w") as outfile:
            writer = csv.writer(outfile)
            outfile.write(("datetime", "x", "y", "z"))
            for index in range(len(timestamp)):
                writer.writerow([timestamp[index],
                                 medx[index],
                                 medy[index],
                                 medz[index]])
        return outputFilename

def main():
    if len(sys.argv) < 2:
        root = tk.Tk()
        root.withdraw()
        filePath = filedialog.askopenfilename(
            filetypes = [("Comma separated file (CSV) format",".csv")])
        window = 25
    else:
        parser = argparse.ArgumentParser(description=
                                         "Convert accelerometer file to per second values")
        parser.add_argument("filename", help="Input filename")
        parser.add_argument("--window", help="Window size", type=int, default="25")
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

