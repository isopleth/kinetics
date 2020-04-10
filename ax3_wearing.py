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
# Alex's filter for detecting sleeve not worn.
#
# "My thought is to apply a filter which takes the highest
# acceleration value for each second and presents this. We could then
# apply a threshold value from sample data that would classify
# movement or not. Periods of say longer than 10 mins with no value
# over threshold could then be classed as 'not wearing' (or completely
# immobile)."
#

# Axes:
# X is the long axis
# Y is the across-the-device axis
# Z is across the thickness of the device

from Row import Row
from tkinter import filedialog
import argparse
import csv
import matplotlib.dates as mdate
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import tkinter as tk

class Processor:

    def makeOutFile(self, filename, threshold):
        """ Make output filename """
        path, file = os.path.split(filename)
        name, ext = os.path.splitext(file)
        newName = "wearing_" + str(threshold) + "_" + name;

        newPlotName = newName + ".pdf"
        newName = newName + ".csv"

        plotFilePath = os.path.join(path, newPlotName)
        dataFilePath = os.path.join(path, newName)
        print("Plot file is", plotFilePath)
        print("Output file is", dataFilePath)
        return [plotFilePath, dataFilePath]

    def _plot(self, plotFilename,
              threshold,
              epochTimestamps,
              maxAccPerSecond,
              aboveThresholdValues,
              inUse):
        """ Generate the plot """

        # Index 0 of data is epoch time
        seconds = mdate.epoch2num(epochTimestamps)
        print(seconds)
        dateFormat = "%H:%M"
        dateFormatter = mdate.DateFormatter(dateFormat)
        locator = mdate.HourLocator(interval=6)
        locator.MAXTICKS = 5000

        fig, axis = plt.subplots(3)

        for index in range(3):
            axis[index].grid(True)
            axis[index].xaxis.set_major_locator(locator)
            axis[index].xaxis.set_minor_locator(mdate.HourLocator())
            axis[index].xaxis.set_major_formatter(dateFormatter)
            axis[index].set_xlabel("Time")

        axis[0].set_title(f"Threshold for total acc = {threshold}g")
        axis[0].set_ylabel("Acceleration (g)")
        axis[0].plot(seconds, maxAccPerSecond, label="max total acc")

        axis[1].set_yticks([0,1])
        axis[1].set_yticklabels(["false","true"])
        axis[1].set_ylabel("Above threshold")
        axis[1].plot(seconds, aboveThresholdValues, label="above threshold")

        axis[2].set_yticks([0,1])
        axis[2].set_yticklabels(["false","true"])
        axis[2].set_ylabel("Above threshold")
        axis[2].plot(seconds, inUse, label="in use")

        plt.legend()
        plt.savefig(plotFilename)
        plt.draw()
        plt.close()


    def __call__(self, filename, threshold):
        """ Process the file """
        # Count number of seconds in the file
        count = 0
        firstEpoch = None
        lastEpoch = None
        with open(filename, "rt", newline="\n") as self.fh:
            line = self.fh.readline().strip()
            while line:
                row = Row(line)
                if row.skip:
                    pass
                elif firstEpoch is None:
                    firstEpoch = row.getEpoch()
                line = self.fh.readline().strip()

            lastEpoch = row.getEpoch()
        secondsInFile = int(lastEpoch) - int(firstEpoch) + 1
        days = round(secondsInFile / 86400, 1)
        print(f"File contains {days} days ({secondsInFile} seconds) worth of data")

        epochTimestamps = np.zeros(secondsInFile)
        maxAccPerSecond = np.zeros(secondsInFile)
        firstSecondEpoch = int(firstEpoch)

        # Now scan through the file and pick out the highest acceleration
        # in each second
        with open(filename, "rt", newline="\n") as self.fh:
            line = self.fh.readline().strip()
            while line:
                row = Row(line)
                if row.skip:
                    pass
                else:
                    second = int(row.getEpoch()) - firstSecondEpoch
                    epochTimestamps[second] = int(row.getEpoch())
                    totalAcc = row.getTotAcc()
                    if totalAcc > maxAccPerSecond[second]:
                        maxAccPerSecond[second] = totalAcc
                line = self.fh.readline().strip()
        print(f"Max per second accelerations extracted")
        aboveThresholdValues = np.copy(maxAccPerSecond)
        # Now scan through looking for movement above a threshold
        for second in range(len(aboveThresholdValues)):
            if aboveThresholdValues[second] < threshold:
                aboveThresholdValues[second] = 0

        print(f"Determining periods of movement")
        # Scan through the above threshold values to set +/-5 minutes to
        # 1 when there is an above threshold value
        inUse = np.zeros(secondsInFile)
        for second in range(len(aboveThresholdValues)):
            if aboveThresholdValues[second] > 0:
                # Set the previous 5 * 60 values, less one, to 1
                backIndex = second - ((4 * 60) + 59)
                for index in range(backIndex, second):
                    inUse[index] = 1
                # Set the next 5 * 60 values to 1
                for index in range(second, second + (5*60)):
                    aboveThresholdValues[second] = 1

        plotFilename, outputFilename = self.makeOutFile(filename, threshold)
        self._plot(plotFilename,
                   threshold,
                   epochTimestamps,
                   maxAccPerSecond,
                   aboveThresholdValues,
                   inUse)

        # Output this as a data file
        outfile = open(outputFilename, "w")
        with outfile:
            writer = csv.writer(outfile)
            for second in range(len(aboveThresholdValues)):
                writer.writerow([int(firstEpoch) + second,
                                 second,
                                 round(maxAccPerSecond[second],6),
                                 aboveThresholdValues[second],
                                 inUse[second]])

        return [plotFilename, outputFilename]

def main():
    """ Command line entry point
    """
    parser = argparse.ArgumentParser(description=
                                     "Descriptive statistics for accelerometer file")
    parser.add_argument("filename", help="Input filename")
    parser.add_argument("threshold", help="Threshold",  nargs="?",
                        type=float, default="1")
    args = parser.parse_args()
    filePath = args.filename
    name, extension =  os.path.splitext(filePath)

    if extension == ".CWA":
        print("You need the .csv, not the .CWA", file=stderr)
        os.exit(0)

    processor = Processor()
    plotfile, datafile = processor(args.filename, args.threshold)

if __name__ == "__main__":
    main()

