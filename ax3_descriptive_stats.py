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
# X is the long axss
# Y is the across-the-device axis
# Z is the across-the-device axis
import numpy as np
import argparse
import sys
from tkinter import filedialog
import tkinter as tk

from Row import Row

class Processor:
        
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

        self.timestamp = np.array(['abba' for _ in range(count)])
        self.epoch = np.zeros((count,))
        self.x = np.zeros((count,))
        self.y = np.zeros((count,))
        self.z = np.zeros((count,))
        self.tot = np.zeros((count,))

        with open(filename, "r") as self.fh:
            line = self.fh.readline().strip()
            index = 0
            while line:
                row = Row(line)
                if row.skip:
                    pass
                else:
                    self.timestamp = self.timestamp
                    self.epoch = row.getEpoch()

                    self.x[index] = row.val[0]
                    self.y[index] = row.val[1]
                    self.z[index] = row.val[2]
                    self.tot[index] = row.getTotAcc()
                    index += 1
                line = self.fh.readline().strip()

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
                
                
def descriptive(type, array):
    """ Summarise array"""
    while len(type) < 6:
        type = type + " "
    print(f"{type} -- n={array.size}, min={array.min():.2f}, max={array.max():.2f}, mean={array.mean():.2f}, std dev={array.std():.2f}, peak to peak={array.ptp():.2f}")
                
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

    processor = Processor()
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


    
if __name__ == "__main__":
    main()
  
