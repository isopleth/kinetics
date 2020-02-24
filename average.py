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
# Read and average Axivity accerometer CSV file.
# Reads a .csv file containing <yyyy-mm-dd hh-mm-ss>
#
# Uses a YAML format configuration file, which looks like this:
#
# resolution: 1
# cutoff: 0.01
#
# Resolution is the number of decimal places to average data into. e.g.
# If set to 1, then all readings taken in a given tenth of a second are
# averaged together in the output file.  It has got to be a power of 10
# to be meaningful
#
# Cutoff is the cut-off frequency of the high pass filter in Hertz. Set
# to zero if you don't want a high pass filter.
#

from calendar import timegm
from datetime import datetime, timedelta
from decimal import Decimal
from math import modf, sqrt
from os import path
from scipy import signal
import numpy as np
from tkinter import filedialog
import argparse
import array
import io
import sys
import time
import tkinter as tk
import yaml

class Row:
    """ Represents a row from the input file
    """
    
    def __init__(self, line):
        """ Constructor - strictly speaking initializer
        """
        # True if this row is to be skipped because it contains a syntax
        # error etc
        self.skip = False
        self._epoch = None
        self._totalAcc = None
        self.timestamp = None

        fields = line.split(",")
        if len(fields) != 4:
            print(f"Ignore {line}, {len(fields)} fields", file=sys.stderr)
            self.skip = True
            return
            
        self.timestamp = fields[0].strip()
        try:
            self.val = array.array('d', [Decimal(fields[1]),
                                         Decimal(fields[2]),
                                         Decimal(fields[3])])
        except ValueError:
            print(f"Conversion error, ignore {line}", file=sys.stderr)
            self.skip = True


    def __str__(self):
        """ String representation of row"""
        return "{},{:.03f},{:.06f},{:.06f},{:.06f},{:.06f}".format(
            self.timestamp, self.getEpoch(), self.val[0],
            self.val[1], self.val[2], self.getTotAcc())
            
    def getEpoch(self):
        """ Get the timestamp as an epoch, seconds since 1/1/1970
        """
        if self.skip:
            return None
        # Lazy evaluation
        if self._epoch is None:
            timestring, dot, milliseconds = self.timestamp.partition('.')

            dateObject = time.strptime(timestring, "%Y-%m-%d %H:%M:%S")
            self._epoch = time.mktime(dateObject) + int(milliseconds) / 1000
        return self._epoch

    def getTotAcc(self):
        """ Get total acceleration for the three x,y,z values.
        """
        if self.skip:
            return None
        # Lazy evaluation
        if self._totalAcc is None:
            self._totalAcc = 0
            for val in self.val:
                self._totalAcc = self._totalAcc + val*val
            self._totalAcc = sqrt(self._totalAcc)
        return self._totalAcc

class OutputRow:
    """This represents a row in the output file """

    def __init__(self, row, resolution):
        if not self._isPowerOf10(resolution):
            print("resolution is %d, which is not supported" % resolution,
                  file=sys.stderr)
            exit(0)
        self.resolution = resolution
        self.epoch = self.truncate(row.getEpoch(), resolution)

        self.val = array.array('d', [0,0,0,0,0,0,0,0])
        self._count = 0
        self.add(row)

    def _isPowerOf10(self, value):
        """Check if value is a power of 10
        """
        if value == 10:
            return True
        elif value <= 1:
            return self._isPowerOf10(value * 10)
        elif value >= 100:
            return self._isPowerOf10(value / 10)
        return False

        
    def add(self, row):
        """Add a row
        """
        self._count = self._count + 1
        for index in range(3):
            self.val[index] = self.val[index] + row.val[index]
        self.val[3] = self.val[3] + row.getTotAcc()

    def goodTime(self, row):
        """Return True if the row has a timestamp inside the range for this
        OutputRow. This is used to decide whether the add this row to the
        OutputRow using the add() method, or to output this OutputRow
        and start another one with this row.
        """
        return self.epoch == self.truncate(row.getEpoch(), self.resolution)

    def calculateMeans(self):
        """ Calculate the means of the first four columns from the already
        computed sums. """
        if self._count != 0:
             for index in range(4):
                self.val[index] = self.val[index] / self._count
        
    def __str__(self):
        """Return a string represention of the output row.
        """
        fraction, integer = modf(self.epoch)
        timestamp = datetime.fromtimestamp(integer).strftime("%Y-%m-%d %H:%M:%S")
        zero, dot, milliseconds = str(round(fraction,3)).partition('.')
        timestamp = timestamp + "." + milliseconds
       
        retval = f"{timestamp},{self.epoch}"
        for val in self.val:
            retval = retval + ",{:.06f}".format(val)
        return retval

    def truncate(self, number, digits):
        """ Remove the integer portion of a floating point number
        """
        fractionalPart = repr(number).find('.')
        if fractionalPart == -1:  
            return int(number) 
        return float(repr(number)[:fractionalPart + digits + 1])
    
class Averager:
    """ This class is the main class of the program.  It processes the
    input file and produces the list of rows to be written to the output
    file"""
    def __init__(self, filename,
                 resolution=1,
                 cutoff=None,
                 verbose=False,
                 limit=None,
                 version=False):

        if not path.exists(filename):
            print("File does not exist", file=sys.stderr)
            return linesGenerated

        if version:
            print("average.py, version 1.01")

        linesGenerated = 0
        if len(filename) == 0:
            print("No filename specified", file=sys.stderr)
            return linesGenerated

        linesRead = 0
        outputRow = None

        self._outputRows = []
        with open(filename, "r") as self.fh:
            line = self.fh.readline()
            while line:
                row = Row(line)

                linesRead += 1
                if linesRead % 1000000 == 0 and linesRead != 0:
                    print(f"{linesRead} lines read")
                    
                if row.skip:
                    # Bad row
                    continue
                
                if outputRow is None:
                    # Starting a new output row
                    outputRow = OutputRow(row, resolution)
                elif outputRow.goodTime(row):
                    outputRow.add(row)
                else:
                    outputRow.calculateMeans()
                    self._outputRows.append(outputRow)
                    outputRow = None
                    if limit is not None and len(self._outputRows) >= limit:
                        break
                line = self.fh.readline()
                
        # High pass filter x,y,z values
        self._filter(resolution, cutoff, self._outputRows, 0, 4)
        self._filter(resolution, cutoff, self._outputRows, 1, 5)
        self._filter(resolution, cutoff, self._outputRows, 2, 6)
        # Total acceleration values
        self._totalAcc(self._outputRows, [4, 5, 6], 7)
        

    def __call__(self):
        """ Return the output rows
        """
        return self._outputRows

    def _filter(self, resolution, cutoff, outputRows, inputIndex, outputIndex):
        """ Apply a high pass filter to outputRows[].val[inputIndex],
        putting the result in outputRows[].val[outputIndex].
        """
        # Convert cutoff in Hz to cutoff as a proportion of sample rate.
        # Resolution is the number of decimal places, so convert that to
        # seconds.
        sampleRate = 1
        power = resolution
        while power > 0:
            sampleRate *= 10
            power = power - 1

        nyquist = 0.5 * sampleRate
        b, a = signal.butter(4, cutoff / nyquist, "high")

        input = np.zeros(len(outputRows))
        for index in range(len(outputRows)):
            input[index] = outputRows[index].val[inputIndex]
            
        output = signal.lfilter(b, a, input) 
        for index in range(len(outputRows)):
            outputRows[index].val[outputIndex] = output[index]

    def _totalAcc(self, outputRows, inputIndexes, outputIndex):
        """ Populate column outputIndex of outputRows with the total
        acceleration of outputRows[inputIndexes], where inputIndexes 
        is a list of indexes
        """
        for index in range(len(outputRows)):
            val = 0
            for column in inputIndexes:
                square = outputRows[index].val[column]
                square *= square
                val += square
            outputRows[index].val[outputIndex] = sqrt(val)
            
def main():

    configurationFile = "configuration.txt"
    if len(sys.argv) < 2:
        root = tk.Tk()
        root.withdraw()
        filePath = filedialog.askopenfilename(
            filetypes = [("Comma separated file (CSV) format",".csv")])
        verbose = False
        limit = None
        version = False
    else:
        parser = argparse.ArgumentParser(description=
                                         "Average down samples in CSV file")
        parser.add_argument("filename",
                            help="Input filename")
        parser.add_argument("--verbose",
                            help="Verbose output",
                            action="store_true")
        parser.add_argument("--limit",
                            help="Stop after this number of output lines",
                            type=int)
        parser.add_argument("--version",
                            help="Display program version",
                            action="store_true")
        parser.add_argument("--config",
                            help="Configuration filename",
                            type=str)
        args = parser.parse_args()
        filePath = args.filename
        verbose = args.verbose
        limit = args.limit
        version = args.version
        if args.config is not None:
            configurationFile = args.config

    with open(configurationFile) as file:
        configuration = yaml.load(file, Loader=yaml.FullLoader)

    outputFilename = path.splitext(filePath)[0] + "_out.csv"
    print(f"Converting {filePath}, output is {outputFilename}")

    averager = Averager(filePath,
                        resolution=configuration["resolution"],
                        cutoff=configuration["cutoff"],
                        verbose=verbose,
                        limit=limit,
                        version=version)

    outputLines = averager()

    with open(outputFilename, "w") as file:
        for line in outputLines:
            print(line, file=file)

    print(f"{len(outputLines)} lines of output generated")

if __name__ == "__main__":
    main()



