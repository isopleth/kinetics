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
from tkinter import filedialog
import argparse
import configparser
import csv
import matplotlib.pyplot as plt
import numpy as np
import sys
import tkinter as tk
import os

class Processor:

    def process(self, filename, controlFile):
        """Process a CSV file of per-minute data as produced by ax3_stats.py.
        controlFile, if specified, is an INI file that controls the
        generation of short plots as well as the normal ones. It contains
        the following in the section [PLOT] -- start is the minute to
        start "short" plot, end -- is the minute to end the "short" plot """

        # e.g. fred/minutes_2020-10-20.csv gives path = fred, suffix =
        # 2020-10-20
        path, name = os.path.split(filename)
        prefix = os.path.splitext(name)[0]
        suffixIndex = len(prefix.split("_"))
        suffix = prefix.split("_")[suffixIndex - 1]
        if suffix is None:
            suffix = ""

        config = configparser.ConfigParser()
        if controlFile is not None:
            if path.exists(controlFile):
                config.read(controlFile)
            else:
                print(f"Control file {controlFile} not found", file=sys.stderr)
                sys.exit(1)

        # Numpy CSV reader
        data = np.genfromtxt(filename, delimiter=",")

        baselined = data[0][18] != 0

        title = [ "minute", "size",
                  "Mean of x acceleration over minute",
                  "peak to peak of x acceleration over minute",
                  "RMS of x acceleration over minute",
                  "std dev of x acceleration over minute",
                  "Mean of y acceleration over minute",
                  "peak to peak of y acceleration over minute",
                  "RMS of y acceleration over minute",
                  "std dev of y acceleration over minute",
                  "Mean of z acceleration over minute",
                  "peak to peak of z acceleration over minute",
                  "RMS of z acceleration over minute",
                  "std dev of z acceleration over minute",
                  "Mean of tot acceleration over minute",
                  "peak to peak of tot acceleration over minute",
                  "RMS of tot acceleration over minute",
                  "std dev of tot acceleration over minute"]

        fileTitle = [ "", "",
                  "mean_x",
                  "peak_to_peak_x",
                  "rms_x",
                  "std_dev_x",
                  "mean_y",
                  "peak_to_peak_y",
                  "rms_y",
                  "std_dev_y",
                  "mean_z",
                  "peak_to_peak_z",
                  "rms_z",
                  "std_dev_z",
                  "mean_total",
                  "peak_to_peak_total",
                  "rms_total",
                  "std_dev_total"]

        # All the interesting stuff happens in the first few mins in
        # some datasets
        if config.has_section("PLOT"):
            if config.has_option("PLOT", "start"):
                start = int(config.get("PLOT", "start"))
            else:
                start = 0

            if config.has_option("PLOT", "end"):
                end = int(config.get("PLOT", "end"))
            else:
                start = len(data) - 1

            if config.has_option("PLOT", "xlines"):
                xlines = config.get("PLOT","xlines")
            else:
                xlines = None
            xlinesList = xlines.split(',')
            truncated = data[start:end]
            for index in range(2, len(title)):
                theTitle = title[index]
                if baselined:
                    theTitle = "Baselined " + theTitle
                plt.title(theTitle)
                for line in xlinesList:
                    line = int(line.strip())
                    plt.axvline(line ,c="red")
                plt.xlabel("minute")
                plt.plot(truncated[:, [index]])
                plt.savefig(self.makeOutFile(
                    baselined,
                    path,
                    "subsection_" +
                    fileTitle[index] + "_" + suffix))
                plt.draw()
                plt.close()
        else:
            xlinesList = []

        # For the full dataset
        for index in range(2, len(title)):
            theTitle = title[index]
            if baselined:
                theTitle = "Baselined " + theTitle
            plt.title(theTitle)
            for line in xlinesList:
                line = int(line.strip())
                plt.axvline(line, c="red")
            plt.xlabel("minute")
            plt.plot(data[:, [index]])
            plt.savefig(self.makeOutFile(
                baselined,
                path,
                "plot_" +
                fileTitle[index] + "_" + suffix))
            plt.draw()
            plt.close()

    def makeOutFile(self, baselined, path, filename):
        """ Make output filename """
        if baselined:
            filename = "baselined_" + filename
        fullPath = os.path.join(path, filename + ".pdf")
        print("Output file is", fullPath)
        return fullPath

def main():
    controlFile = None
    if len(sys.argv) < 2:
        root = tk.Tk()
        root.withdraw()
        filePath = filedialog.askopenfilename(
            filetypes = [("Comma separated file (CSV) format",".csv")])
    else:
        parser = argparse.ArgumentParser(description=
                                         "Plot statistics for accelerometer file")
        parser.add_argument("filename", help="Input filename")
        parser.add_argument("--controlfile", nargs="?", help="INI file to control plotting")
        args = parser.parse_args()
        filePath = args.filename
        controlFile = args.controlfile

    processor = Processor()
    processor.process(filePath, controlFile)

if __name__ == "__main__":
    main()

