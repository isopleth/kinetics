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
# Descriptive statistics for accelerometer file
#

# Axes:
# X is the long axis
# Y is the across-the-device axis
# Z is across the thickness of the device
import numpy as np
import argparse
import sys
from tkinter import filedialog
import tkinter as tk
import csv
from Row import Row
import os

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
        rowAbove8 = [0,0,0]
        rowAbove7 = [0,0,0]
        rowAbove6 = [0,0,0]
        rowAbove1 = [0,0,0]

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
                        print(f"{index} lines read")

                    for axis in range(len(row.val)):
                        if abs(row.val[axis]) >= 8:
                            rowAbove8[axis] = rowAbove8[axis] + 1
                        if abs(row.val[axis]) >= 7:
                            rowAbove7[axis] = rowAbove7[axis] + 1
                        if abs(row.val[axis]) >= 6:
                            rowAbove6[axis] = rowAbove6[axis] + 1
                        if abs(row.val[axis]) >= 1:
                            rowAbove1[axis] = rowAbove1[axis] + 1
                line = self.fh.readline().strip()

        for axis in range(len(row.val)):
            # size of x is the same as y and z
            proportion = rowAbove8[axis]/self.x.size
            print(f"axis {axis}, +/-8 or more {rowAbove8[axis]} times")
            print(f"axis {axis}, +/-7 or more {rowAbove7[axis]} times")
            print(f"axis {axis}, +/-6 or more {rowAbove6[axis]} times")
            print(f"axis {axis}, +/-1 or more {rowAbove1[axis]} times")
        print()

        outputFilename = self.makeOutFile(filename, self.firstLine)
        outfile = open(outputFilename, "w")
        with outfile:
            writer = csv.writer(outfile)
            for index in range(self.epoch.size):
                writer.writerow([self.epoch[index], self.x[index],
                                 self.y[index], self.z[index],
                                 self.tot[index]])
        return outputFilename

    def subtractMeans(self):
        meanx = self.x.mean()
        meany = self.y.mean()
        meanz = self.z.mean()
        meant = self.tot.mean()
        for index in range(0, self.x.size):
            self.x[index] = self.x[index] - meanx
            self.y[index] = self.y[index] - meany
            self.z[index] = self.z[index] - meanz
            self.tot[index] = self.tot[index] - meant

class Minutes:
    """ This class converts the accelerometer data read by the StatsProcessor
    class into the per-minute data """

    def makeOutFile(self, processor, baseline):
        """ Make output filename """
        path = os.path.split(processor.filename)[0]
        startDate = processor.firstLine.split()[0]
        newName = ""
        if baseline :
            newName = "baselined_"
        newName = newName + "minutes_" + startDate + ".csv"
        fullPath = os.path.join(path, newName)
        print("Output file is", fullPath)
        return fullPath

    def process(self, processor, baseline):
        """Process the data.  Processor is the StatsProcessor object,
        baseline is True if each minute of data is to be baselined

        """
        self.startMinute = self.toMinute(processor.epoch[0])
        self.endMinute = self.toMinute(processor.epoch[processor.epoch.size - 1])
        self.interval = int(self.endMinute - self.startMinute + 1)
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

        # Count the number of samples in each minute and accumulate that
        # in an array which is going to be used to size the individual
        # arrays for each minute
        for index in range(0, processor.x.size):
            minute = self.toMinute(processor.epoch[index]) - self.startMinute
            self.size[minute] = self.size[minute] + 1

        # Now create the numpy arrays for each minute with the correct size
        for minute in range(self.interval):
            self.x.append(np.zeros((int(self.size[minute]),)))
            self.y.append(np.zeros((int(self.size[minute]),)))
            self.z.append(np.zeros((int(self.size[minute]),)))
            self.tot.append(np.zeros((int(self.size[minute]),)))
            self.check.append(np.zeros((int(self.size[minute]),)))
            
        for index in range(processor.x.size):
            minute = self.toMinute(processor.epoch[index]) - self.startMinute
            if self.epoch[minute] == 0:
                # Epoch time is the minute as epoch time
                self.epoch[minute] = int(self.toMinute(processor.epoch[index]) * 60)
            rowIndex = int(self.currentIndex[minute])
            self.x[minute][rowIndex] = processor.x[index]
            self.y[minute][rowIndex] = processor.y[index]
            self.z[minute][rowIndex] = processor.z[index]
            self.tot[minute][rowIndex] = processor.tot[index]
            self.check[minute][rowIndex] = 1
            self.currentIndex[minute] = rowIndex + 1

        ## print()
        ## print(f"Points per minute are {self.currentIndex-1}")

        # This is a sanity check to make sure that all values in
        # all minutes are filled in.  It should not output anything
        for minute in range(self.interval):
            for index in range(len(self.check[minute])):
                if self.check[minute][index] != 1:
                    print(f"Check index {index} at minute {minute}!!!")

        # Baseline
        if baseline:
            for minute in range(self.interval):
                xmean = self.x[minute].mean()
                ymean = self.y[minute].mean()
                zmean = self.z[minute].mean()
                totmean = self.tot[minute].mean()

                self.x[minute] = self.x[minute] - xmean
                self.y[minute] = self.y[minute] - ymean
                self.z[minute] = self.z[minute] - zmean
                self.tot[minute] = self.tot[minute] - totmean
                baselineVal = 1
            else:
                baselineVal = 0
                
        outputFilename = self.makeOutFile(processor, baseline)
        outfile = open(outputFilename, "w")
        with outfile:
            print()
            print("fields in CSV file are: " +
                  "epoch," +
                  "minute," +
                  "size," +
                  "x mean," +
                  "x rms," +
                  "x peak to peak," +
                  "x std dev," +
                  "y mean," +
                  "y rms," +
                  "y peak to peak," +
                  "y std dev," +
                  "z mean," +
                  "z rms," +
                  "z peak to peak," +
                  "z std dev," +
                  "tot mean," +
                  "tot rms," +
                  "tot peak to peak," +
                  "tot std dev," +
                  "is baselined flag")

            writer = csv.writer(outfile)
            for minute in range(0, self.interval):
                rmsx = np.sqrt(np.mean(np.square(self.x[minute])))
                rmsy = np.sqrt(np.mean(np.square(self.y[minute])))
                rmsz = np.sqrt(np.mean(np.square(self.z[minute])))
                rmstot = np.sqrt(np.mean(np.square(self.tot[minute])))
                baselineVal = 0
                if baseline:
                    baselineVal = 1
                if self.x[minute].size == 0:
                    print(f"No data for minute {minute}")
                else:
                    writer.writerow([self.epoch[minute],
                                     minute,
                                     self.x[minute].size,
                                     self.x[minute].mean(),
                                     self.x[minute].ptp(),
                                     rmsx,
                                     self.x[minute].std(),
                                     self.y[minute].mean(),
                                     self.y[minute].ptp(),
                                     rmsy,
                                     self.y[minute].std(),
                                     self.z[minute].mean(),
                                     self.z[minute].ptp(),
                                     rmsz,
                                     self.z[minute].std(),
                                     self.tot[minute].mean(),
                                     self.tot[minute].ptp(),
                                     rmstot,
                                     self.tot[minute].std(),
                                     baselineVal])
        return outputFilename

    def toMinute(self, second):
        """ Convert epoch seconds to minutes """
        minute = second // 60
        return int(minute)

def summarise(type, array):
    """ Summarise array"""
    while len(type) < 6:
        type = type + " "
    print(f"{type} -- n={array.size}, min={array.min():.2f}, " +
          f"max={array.max():.2f}, mean={array.mean():.2f}, " +
          f"std dev={array.std():.2f}, peak to peak={array.ptp():.2f}")

def stats(filePath):
    """ Main processing function
    """
    processor = StatsProcessor()
    datafile = processor.process(filePath)
    print("---descriptive stats---")
    summarise("x", processor.x);
    summarise("y", processor.y);
    summarise("z", processor.z);
    summarise("total", processor.tot);
    print()
    # This used to subtract the mean from each value
    # print("---Subtract mean from each value to baseline---")
    # processor.subtractMeans()
    # summarise("x", processor.x);
    # summarise("y", processor.y);
    # summarise("z", processor.z);
    # summarise("total", processor.tot);

    minutes = Minutes()
    # Run without baselining the minutes data
    nonBaselinedFile = minutes.process(processor, False)
    baselinedFile = minutes.process(processor, True)
    print(f"Dataset is {minutes.interval} minutes long")
    return [ datafile, nonBaselinedFile, baselinedFile ]
    
def main():
    """ Command line entry point
    """
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

    datafile, nonBaselinedFile, baselinedFile = stats(filePath)
    print()
    print("Raw data output file is", datafile)
    print("Minutes data output file is", nonBaselinedFile)
    print("Baselined minutes data output file is", baselinedFile)
    
if __name__ == "__main__":
    main()

