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
# Z is the across-the-device axis
import numpy as np
import argparse
import sys
from tkinter import filedialog
import tkinter as tk
import csv

from Row import Row

class StatsProcessor:
        
    def process(self, filename):
        # Count number of lines in file to get array dimension
        count = 0
        with open(filename, "r") as self.fh:
            line = self.fh.readline().strip()
            while line:
                row = Row(line)
                if row.skip:
                    pass
                else:
                    count += 1
                line = self.fh.readline().strip()

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

        with open(filename, "r") as self.fh:
            line = self.fh.readline().strip()
            index = 0
            while line:
                row = Row(line)
                if row.skip:
                    pass
                else:
                    self.timestamp[index] = row.timestamp
                    self.epoch[index] = row.getEpoch()

                    self.x[index] = row.val[0]
                    self.y[index] = row.val[1]
                    self.z[index] = row.val[2]
                    self.tot[index] = row.getTotAcc()
                    index += 1

                    for iindex in range(len(row.val)):
                        if abs(row.val[iindex]) >= 8:
                            rowAbove8[iindex] = rowAbove8[iindex] + 1
                        if abs(row.val[iindex]) >= 7:
                            rowAbove7[iindex] = rowAbove7[iindex] + 1
                        if abs(row.val[iindex]) >= 6:
                            rowAbove6[iindex] = rowAbove6[iindex] + 1
                        if abs(row.val[iindex]) >= 1:
                            rowAbove1[iindex] = rowAbove1[iindex] + 1
                line = self.fh.readline().strip()

        for iindex in range(len(row.val)):
            # size of x is the same as y and z
            proportion = rowAbove8[iindex]/self.x.size            
            print(f"axis {iindex}, +/-8 or more {rowAbove8[iindex]} times")
            print(f"axis {iindex}, +/-7 or more {rowAbove7[iindex]} times")
            print(f"axis {iindex}, +/-6 or more {rowAbove6[iindex]} times")
            print(f"axis {iindex}, +/-1 or more {rowAbove1[iindex]} times")
                
        f = open("accelerometer.csv", "w")
        with f:
            writer = csv.writer(f)
            for index in range(self.epoch.size):
                writer.writerow([self.epoch[index], self.x[index],
                                 self.y[index], self.z[index],
                                 self.tot[index]])


                
    def  subtractMeans(self):
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
    def __init__(self, processor):
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
            min = self.toMinute(processor.epoch[index]) - self.startMinute
            self.size[min] = self.size[min] + 1

        # Now create the numpy arrays for each minute with the correct size
        for min in range(self.interval):
            self.x.append(np.zeros((int(self.size[min]),)))
            self.y.append(np.zeros((int(self.size[min]),)))
            self.z.append(np.zeros((int(self.size[min]),)))
            self.tot.append(np.zeros((int(self.size[min]),)))
            self.check.append(np.zeros((int(self.size[min]),)))

        for index in range(processor.x.size):            
            min = self.toMinute(processor.epoch[index]) - self.startMinute
            rowIndex = int(self.currentIndex[min])
            self.x[min][rowIndex] = processor.x[index]
            self.y[min][rowIndex] = processor.y[index]
            self.z[min][rowIndex] = processor.z[index]
            self.tot[min][rowIndex] = processor.tot[index]
            self.check[min][rowIndex] = 1
            self.currentIndex[min] = rowIndex + 1

        print()
        print(f"Points per minute are {self.currentIndex-1}")
        
        # This is a sanity check to make sure that all values in
        # all minutes are filled in.  It should not output anything
        for min in range(self.interval):
            for index in range(len(self.check[min])):
                if self.check[min][index] != 1:
                    print(f"Check index {index} at minute {min}!!!")

        f = open("minutes.csv", "w")
        with f:
            print()
            print("Minute,"+
                  "size,"+
                  "x mean,"+
                  "x rms,"+
                  "x peak to peak,"+
                  "x std dev,"+
                  "y mean,"+
                  "y rms,"+
                  "y peak to peak,"+
                  "y std dev,"+
                  "z mean,"+
                  "z rms,"+
                  "z peak to peak,"+
                  "z std dev,"+
                  "tot mean,"+
                  "tot rms,"+
                  "tot peak to peak,"+
                  "tot std dev")

            writer = csv.writer(f)
            for min in range(0, self.interval):
                rmsx = np.sqrt(np.mean(np.square(self.x[min])))
                rmsy = np.sqrt(np.mean(np.square(self.y[min])))
                rmsz = np.sqrt(np.mean(np.square(self.z[min])))
                rmstot = np.sqrt(np.mean(np.square(self.tot[min])))
                      
                #print(f"{min}, {self.x[min].size}," +
                #      f" {self.x[min].mean():.3f}," +
                #      f" {self.x[min].ptp():.3f}," +
                #      f" {rmsx:.3f}," +
                #      f" {self.x[min].std():.3f}," +
                #      f" {self.y[min].mean():.3f}," +
                #      f" {self.y[min].ptp():.3f}," +
                #      f" {rmsy:.3f}," +
                #      f" {self.y[min].std():.3f}," +
                #      f" {self.y[min].mean():.3f}," +
                #      f" {self.y[min].ptp():.3f}," +
                #      f"{rmsz:.3f}," +
                #      f"{self.z[min].std():.3f}," +
                #      f" {self.tot[min].mean():.3f}," +
                #      f" {self.tot[min].ptp():.3f}," +
                #      f" {rmstot:.3f}," +
                #      f"{self.tot[min].std():.3f}," +
                #      f" {rmsx:.3f}")
                writer.writerow([min,
                                 self.x[min].size,
                                 self.x[min].mean(),
                                 self.x[min].ptp(),
                                 rmsx,
                                 self.x[min].std(),
                                 self.y[min].mean(),
                                 self.y[min].ptp(),
                                 rmsy,
                                 self.y[min].std(),
                                 self.z[min].mean(),
                                 self.z[min].ptp(),
                                 rmsz,
                                 self.z[min].std(),
                                 self.tot[min].mean(),
                                 self.tot[min].ptp(),
                                 rmstot,
                                 self.tot[min].std()])
            
    def toMinute(self, second):
        """ Convert epoch seconds to minutes """
        minute = second // 60
        return int(minute)
            
def descriptive(type, array):
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
                                         "Descriptive statistics for accerometer file")
        parser.add_argument("filename", help="Input filename")
        args = parser.parse_args()
        filePath = args.filename

    processor = StatsProcessor()
    processor.process(filePath)
    print("---descriptive stats---")
    descriptive("x", processor.x);
    descriptive("y", processor.y);
    descriptive("z", processor.z);
    descriptive("total", processor.tot);
    print()
    print("---Subtract mean from each value to baseline---")
    processor.subtractMeans()
    descriptive("x", processor.x);
    descriptive("y", processor.y);
    descriptive("z", processor.z);
    descriptive("total", processor.tot);

    minutes = Minutes(processor)
    print(f"Dataset is {minutes.interval} minutes long")
    
if __name__ == "__main__":
    main()
  
