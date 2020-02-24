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
# Plot stats from ax3
#

import numpy as np
import argparse
import sys
from tkinter import filedialog
import tkinter as tk
import csv
import matplotlib.pyplot as plt

class Processor:
    def process(self, filename):
        with open(filename, "r") as csvfile:
            reader = csv.reader(csvfile, delimiter=" ", quotechar="#")
            for row in reader:
                print(", ".join(row))
        data = np.genfromtxt(filename, delimiter=",")
        print(data)

        title = [ "minute", "size",
                  "mean of x values over minute",
                  "ptp of x values over minute",
                  "rms of x values over minute",
                  "std dev of x values over minute",
                  "mean of y values over minute",
                  "ptp of y values over minute",
                  "rms of y values over minute",
                  "std dev of y values over minute",
                  "mean of z values over minute",
                  "ptp of z values over minute",
                  "rms of z values over minute",
                  "std dev of z values over minute",
                  "mean of tot values over minute",
                  "ptp of tot values over minute",
                  "rms of tot values over minute",
                  "std dev of tot values over minute"]

                  
        # All the interesting stuff happens in the first 25 minutes
        truncated = data[:40]
        for index in range(2, len(title)):
            plt.title(title[index])
            plt.axvline(4,c="red")
            plt.axvline(12,c="red")
            plt.axvline(20,c="red")
            plt.xlabel("minute")
            plt.plot(truncated[:, [index]])
            plt.show()

        # For the full dataset
        for index in range(2, 13):
            plt.title(title[index])
            plt.axvline(4,c="red")
            plt.axvline(12,c="red")
            plt.axvline(20,c="red")

            plt.xlabel("minute")
            plt.plot(data[:, [index]])
            plt.show()
            
def main():
    if len(sys.argv) < 2:
        root = tk.Tk()
        root.withdraw()
        filePath = filedialog.askopenfilename(
            filetypes = [("Comma separated file (CSV) format",".csv")])
    else:
        parser = argparse.ArgumentParser(description=
                                         "Plot statistics for accelerometer file")
        parser.add_argument("filename", help="Input filename")
        args = parser.parse_args()
        filePath = args.filename

    processor = Processor()
    processor.process(filePath)
    
if __name__ == "__main__":
    main()
  
