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

    def __call__(self, filename):
        """ Process the file """
        print(f"ax3_seconds_stats.py processing {filename}")
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
    """This class converts the accelerometer data read by the
    StatsProcessor class into the per-second data
    """

    def makeMeansOutFile(self, processor):
        """ Make output filename """
        path = os.path.split(processor.filename)[0]
        startDate = processor.firstLine.split()[0]
        newName = "seconds_mean_" + startDate + ".csv"
        fullPath = os.path.join(path, newName)
        print("Output file is", fullPath)
        return fullPath

    def makeRmsOutFile(self, processor):
        """ Make output filename """
        path = os.path.split(processor.filename)[0]
        startDate = processor.firstLine.split()[0]
        newName = "seconds_rms_" + startDate + ".csv"
        fullPath = os.path.join(path, newName)
        print("Output file is", fullPath)
        return fullPath

    def __call__(self, processor):
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

    def writeMeans(self, processor):
        """ Write per-second data calculated using means """
        outputFilename = self.makeMeansOutFile(processor)
        outfile = open(outputFilename, "w")
        noValuesSecs = []
        with outfile:
            writer = csv.writer(outfile)
            writer.writerow(["second",
                             "x_mean",
                             "y_mean",
                             "z_mean",
                             "tot_mean"])

            for sec in range(self.interval):
                if len(self.x[sec]) == 0:
                    noValuesSecs.append(sec)
                else:
                    writer.writerow([sec,
                                 self.x[sec].mean(),
                                 self.y[sec].mean(),
                                 self.z[sec].mean(),
                                 self.tot[sec].mean()])
        if len(noValuesSecs) != 0:
            print(f"No values for {len(noValuesSecs)} one second time periods")
        return outputFilename

    def rms(self, array):
        squareTotal = 0
        for a in array:
            squareTotal = squareTotal + (a * a)
        return math.sqrt(squareTotal / len(array))
    
    def writeRms(self, processor):
        """ Write per-second data calculated using root mean square """
        outputFilename = self.makeRmsOutFile(processor)
        outfile = open(outputFilename, "w")
        noValuesSecs = []
        with outfile:
            writer = csv.writer(outfile)
            for sec in range(self.interval):
                if len(self.x[sec]) == 0:
                    noValuesSecs.append(sec)
                else:
                    writer.writerow([sec,
                                 self.rms(self.x[sec]),
                                 self.rms(self.y[sec]),
                                 self.rms(self.z[sec]),
                                 self.rms(self.tot[sec])])
        if len(noValuesSecs) != 0:
            print(f"RMS - no values for {len(noValuesSecs)} one second time periods")
        return outputFilename

    def toSecond(self, second):
        """ Convert epoch seconds seconds by truncating fractional part """
        return int(math.floor(second))

    def makeSweptOutFile(self, processor, minmax, axis):
        """ Make output filename """
        path = os.path.split(processor.filename)[0]
        startDate = processor.firstLine.split()[0]
        minmax = minmax * 100
        minmax = int(minmax)
        if axis == 0:
            axis = "x"
        elif axis == 1:
            axis = "y"
        elif axis == 2:
            axis = "z"
        elif axis == 3:
            axis = "tot"
        else:
            axis = "unknown"
            
        newName = "seconds_" + str(minmax) + "_" + axis + "_" + startDate + ".csv"
        fullPath = os.path.join(path, newName)
        print("Output file is", fullPath)
        return fullPath

    def checkKeep(self, old, new, minmax):
        absval = abs(old)
        limit = absval * minmax
        lowlim = old - limit
        highlim = old + limit
        if new > highlim or new < lowlim:
            return True
        return False
    
    def sweep(self, minmax, axis):
        """Generate a new file, throwing away values where the next axis
        value differs by less than minmax proportion from the previous
        one

        """
        outputFilename = self.makeSweptOutFile(self.processor, minmax, axis)
        outfile = open(outputFilename, "w")
        with outfile:
            writer = csv.writer(outfile)
            for sec in range(len(self.x)):
                output = True
                if sec > 0:
                    if axis == 0:
                        output = self.checkKeep(self.x[sec-1].mean(), self.x[sec].mean(), minmax)
                    elif axis == 1:
                        output = self.checkKeep(self.y[sec-1].mean(), self.y[sec].mean(), minmax)
                    elif axis == 2:
                        output = self.checkKeep(self.z[sec-1].mean(), self.z[sec].mean(), minmax)
                    elif axis == 3:
                        output = self.checkKeep(self.tot[sec-1].mean(), self.tot[sec].mean(), minmax)
                if output:
                    writer.writerow([sec,
                                 self.x[sec].mean(),
                                 self.y[sec].mean(),
                                 self.z[sec].mean(),
                                 self.tot[sec].mean()])
        return outputFilename
        
    
def summarise(type, array):
    """ Summarise array"""
    while len(type) < 6:
        type = type + " "
    print(f"{type} -- n={array.size}, min={array.min():.2f}, "+
          f"max={array.max():.2f}, mean={array.mean():.2f}, "+
          f"std dev={array.std():.2f}, peak to peak={array.ptp():.2f}")

def process(filePath, limit = 0.05, axis = 3):
    processor = StatsProcessor()
    datafile = processor(filePath)
    print("---descriptive stats---")
    summarise("x", processor.x)
    summarise("y", processor.y)
    summarise("z", processor.z)
    summarise("total", processor.tot)
    print()

    seconds = Seconds()
    seconds(processor)
    secondsMeansFile = seconds.writeMeans(processor)
    secondsRmsFile = seconds.writeRms(processor)
    sweptFile = seconds.sweep(limit, axis)
    print(f"Dataset is {seconds.interval} seconds long")
    print()
    print("Seconds means data output file is", secondsMeansFile)
    print("Seconds RMS data output file is", secondsRmsFile)
    print("Swept file file is", sweptFile)

    return [ secondsMeansFile, secondsRmsFile, sweptFile ]
    
def main():
    if len(sys.argv) < 2:
        root = tk.Tk()
        root.withdraw()
        filePath = filedialog.askopenfilename(
            filetypes = [("Comma separated file (CSV) format",".csv")])
        axis = 3
        limit = 0.05
    else:
        parser = argparse.ArgumentParser(description=
                                         "Convert accelerometer file to per second values")
        parser.add_argument("filename", help="Input filename")
        parser.add_argument("--axis", help="Axis number", type=int, default="3")
        parser.add_argument("--limit", help="+/- limit, default is 5 (percent)", type=int, default="5")
        args = parser.parse_args()
        filePath = args.filename
        name, extension =  os.path.splitext(filePath)
        axis = args.axis
        limit = args.limit
        if axis < 0 or axis > 3:
            print(f"Bad value for axis, {axis}, using 3 (i.e. total")
            axis = 3
        limit = abs(float(limit))
        limit = limit / 100        

        if extension == ".CWA":
            print("You need the .csv, not the .CWA", file=stderr)
            os.exit(0)

    process(filePath, limit, axis)

if __name__ == "__main__":
    main()

