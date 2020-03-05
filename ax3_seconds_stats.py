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
# Z is the across-the-device axis
from Row import Row
from tkinter import filedialog
import argparse
import csv
import math
import numpy as np
import os
import sys
import tkinter as tk

class StatsProcessor:

    def makeOutFile(self, filename, firstLine):
        """ Make output filename """
        path = os.path.split(filename)[0]
        startDate = firstLine.split()[0]
        newName = "accelerometer_" + startDate + ".csv"
        fullPath = os.path.join(path, newName)
        print("Output file is", fullPath)
        return fullPath

    def process(self, filename):
        """ Process the file """
        # Count number of lines in file to get array dimension
        print("Count lines in file")
        count = 0
        with open(filename, "rt", newline="\n") as self.fh:
            line = self.fh.readline().strip()
            while line:
                row = Row(line)
                if row.skip:
                    pass
                else:
                    count += 1
                if count % 1000000 == 0:
                    print(f"{count} lines counted")
                line = self.fh.readline().strip()

        self.filename = filename
        self.timestamp = np.array(["(empty)" for _ in range(count)])
        self.epoch = np.zeros((count,))
        self.x = np.zeros((count,))
        self.y = np.zeros((count,))
        self.z = np.zeros((count,))
        self.tot = np.zeros((count,))

        print("Read file")
        self.firstLine = None
        with open(filename, "rt", newline="\n") as self.fh:
            line = self.fh.readline().strip()
            index = 0
            while line:
                row = Row(line)
                if row.skip:
                     pass
                else:
                    if self.firstLine is None:
                         self.firstLine = row.timestamp
                    self.timestamp[index] = row.timestamp
                    self.epoch[index] = row.getEpoch()
                    self.x[index] = row.val[0]
                    self.y[index] = row.val[1]
                    self.z[index] = row.val[2]
                    self.tot[index] = row.getTotAcc()
                    index += 1
                if index % 1000000 == 0:
                    print(f"{index} data lines read")

                line = self.fh.readline().strip()

class Seconds:
    """ This class converts the accelerometer data read by the StatsProcessor
    class into the per-second data """

    def makeOutFile(self, processor):
        """ Make output filename """
        path = os.path.split(processor.filename)[0]
        startDate = processor.firstLine.split()[0]
        newName = "seconds_" + startDate + ".csv"
        fullPath = os.path.join(path, newName)
        print("Output file is", fullPath)
        return fullPath

    def process(self, processor):
        """Process the data.

        """
        self.startSecond = self.toSecond(processor.epoch[0])
        self.endSecond = self.toSecond(processor.epoch[processor.epoch.size - 1])
        self.interval = int(self.endSecond - self.startSecond + 1)
        self.processor = processor

        self.timestamp = np.array(["(empty)" for _ in range(self.interval)])
        self.epoch = np.zeros((self.interval,))
        self.size = np.zeros((self.interval,))
        self.currentIndex = np.zeros((self.interval,))

        self.x = []
        self.y = []
        self.z = []
        self.tot = []
        # This is just a check that all entries are filled
        self.check = []

        print("Build per second arrays")
        # Count the number of samples in each second and accumulate that
        # in an array which is going to be used to size the individual
        # arrays for each second
        for index in range(0, processor.x.size):
            sec = self.toSecond(processor.epoch[index]) - self.startSecond
            self.size[sec] = self.size[sec] + 1

        # Now create the numpy arrays for each second with the correct size
        for sec in range(self.interval):
            self.x.append(np.zeros((int(self.size[sec]),)))
            self.y.append(np.zeros((int(self.size[sec]),)))
            self.z.append(np.zeros((int(self.size[sec]),)))
            self.tot.append(np.zeros((int(self.size[sec]),)))
            self.check.append(np.zeros((int(self.size[sec]),)))

        for index in range(processor.x.size):
            sec = self.toSecond(processor.epoch[index]) - self.startSecond
            rowIndex = int(self.currentIndex[sec])
            self.x[sec][rowIndex] = processor.x[index]
            self.y[sec][rowIndex] = processor.y[index]
            self.z[sec][rowIndex] = processor.z[index]
            self.tot[sec][rowIndex] = processor.tot[index]
            self.check[sec][rowIndex] = 1
            self.currentIndex[sec] = rowIndex + 1

        print()
        print(f"Points per second are {self.currentIndex-1}")

        # This is a sanity check to make sure that all values in
        # all minutes are filled in.  It should not output anything
        for sec in range(self.interval):
            for index in range(len(self.check[sec])):
                if self.check[sec][index] != 1:
                    print(f"Check index {index} at minute {min}!!!")

        outputFilename = self.makeOutFile(processor)
        outfile = open(outputFilename, "w")
        with outfile:
            writer = csv.writer(outfile)
            for sec in range(0, self.interval):
                writer.writerow([sec,
                                 self.x[sec].mean(),
                                 self.y[sec].mean(),
                                 self.z[sec].mean(),
                                 self.tot[sec].mean()])
        return outputFilename

    def toSecond(self, second):
        """ Convert epoch seconds seconds by truncating fractional part """
        return int(math.floor(second))

def summarise(type, array):
    """ Summarise array"""
    while len(type) < 6:
        type = type + " "
    print(f"{type} -- n={array.size}, min={array.min():.2f}, "+
          f"max={array.max():.2f}, mean={array.mean():.2f}, "+
          f"std dev={array.std():.2f}, peak to peak={array.ptp():.2f}")

def main():
    if len(sys.argv) < 2:
        root = tk.Tk()
        root.withdraw()
        filePath = filedialog.askopenfilename(
            filetypes = [("Comma separated file (CSV) format",".csv")])
    else:
        parser = argparse.ArgumentParser(description=
                                         "Descriptive statistics for accelerometer file")
        parser.add_argument("filename", help="Input filename")
        args = parser.parse_args()
        filePath = args.filename
        name, extension =  os.path.splitext(filePath)

        if extension == ".CWA":
            print("You need the .csv, not the .CWA", file=stderr)
            os.exit(0)

    processor = StatsProcessor()
    datafile = processor.process(filePath)
    print("---descriptive stats---")
    summarise("x", processor.x);
    summarise("y", processor.y);
    summarise("z", processor.z);
    summarise("total", processor.tot);
    print()


    seconds = Seconds()
    # Run without baselining the minutes data
    secondsFile = seconds.process(processor)
    print(f"Dataset is {seconds.interval} seconds long")
    print()
    print("Seconds data output file is", secondsFile)

if __name__ == "__main__":
    main()

