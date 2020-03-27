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
import matplotlib.dates as mdate
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import tkinter as tk

class PlotMinutes:
    """ Produce the minutes plots
    """

    def _plot(self, data, index, xlines, title,
              outputfile, showtime, ymin, ymax, grid):
        """ Generate the actual plot. Returns outputfile
        """
        fig, axis = plt.subplots()
        if ymax is not None or ymin is not None:
            plt.ylim(ymin, ymax)

        axis.grid(grid)
        axis.set_title(title)
        axis.set_ylabel("acceleration (g)")
        for line in xlines:
            line = int(line.strip())
            plt.axvline(line, c="red")

        if showtime:
            # Index 0 of data is epoch time
            seconds = mdate.epoch2num(data[:, [0]])
            dateFormat = "%H:%M"
            dateFormatter = mdate.DateFormatter(dateFormat)
            axis.xaxis.set_major_locator(mdate.HourLocator(interval=6))
            axis.xaxis.set_minor_locator(mdate.HourLocator())
            axis.xaxis.set_major_formatter(dateFormatter)
            fig.autofmt_xdate()
            axis.set_xlabel("time")
            plt.plot(seconds, data[:, [index]])
        else:
            axis.set_xlabel("minute")
            # Index 1 of data is minutes from start
            plt.plot(data[:, [1]], data[:, [index]])
        plt.savefig(outputfile)
        plt.draw()
        plt.close()
        return outputfile

    def __call__(self, filename, controlFile=None, showtime=False,
                 ymin=None, ymax=None, selectedPlot=None, grid=False):
        """Process a CSV file of per-minute data as produced by ax3_stats.py.
        controlFile, if specified, is an INI file that controls the
        generation of short plots as well as the normal ones. It
        contains the following in the section [PLOT] -- start is the
        minute to start "short" plot, end -- is the minute to end the
        "short" plot

        """

        # e.g. fred/minutes_2020-10-20.csv gives path = fred, suffix =
        # 2020-10-20
        path, name = os.path.split(filename)
        prefix = os.path.splitext(name)[0]
        suffixIndex = len(prefix.split("_"))
        suffix = prefix.split("_")[suffixIndex - 1]
        if suffix is None:
            suffix = ""

        outputFiles = []
        
        config = configparser.ConfigParser()
        if controlFile is not None:
            if os.path.exists(controlFile):
                config.read(controlFile)
            else:
                print(f"Control file {controlFile} not found", file=sys.stderr)
                sys.exit(1)

        # Numpy CSV reader
        data = np.genfromtxt(filename, delimiter=",")

        # Baselined flag is in the last field of the CSV file.  Only look
        # at the first row since the value is the same throughout the file
        baselined = data[0][19] != 0

        # These are the fields in the CSV file, except for the last,
        # is_baselined one.  We don't get as far as processing that
        # because we stop when we have exhausted the fileTitle list
        # below
        title = [ "epoch",
                  "minute",
                  "size",
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

        # These are the titles of the graphics files.  Empty string
        # means no file is produced.  Each file plots minutes against
        # the CSV field corresponding to the current index into this
        # array. e.g. mean_x is index 3, so the mean_x file plots
        # minutes against (zero based) column #3, which is the mean x
        # values per minute
        fileTitle = [ "",
                      "",
                      "",
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
        # some datasets.  This is the code for producing plots which
        # are limited and annotated by the optional config file
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
            # xlinesList is the list of X values that have vertical
            # red lines displayed
            xlinesList = xlines.split(',')
            # The subset of points that are to be plotted
            truncated = data[start:end]
            for index in range(3, len(title)):
                if selectedPlot is not None:
                    if selectedPlot != fileTitle[index]:
                        continue
                
                plotTitle = title[index]
                if baselined:
                    plotTitle = "Baselined " + plotTitle

                outputFile = self.makeOutFile(baselined,
                                              path,
                                              "subsection_" +
                                              fileTitle[index] + "_" + suffix)

                outputfiles.append(self._plot(truncated, index, xlinesList,
                                              plotTitle, outputFile,
                                              showtime, ymin, ymax, grid))
        else:
            # Create an empty array so that nothing is plotted
            # in the next block for the full dataset
            xlinesList = []

        # For the full dataset
        for index in range(3, len(title)):
            if selectedPlot is not None:
                if selectedPlot != fileTitle[index]:
                    continue

            plotTitle = title[index]
            if baselined:
                plotTitle = "Baselined " + plotTitle

            outputFile = self.makeOutFile(baselined,
                                          path,
                                          "plot_" +
                                          fileTitle[index] + "_" + suffix)
            
            outputFiles.append(self._plot(data, index, xlinesList,
                                          plotTitle, outputFile,
                                          showtime, ymin, ymax, grid))

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
        controlFile = None
        showtime = None
        ymin = None
        ymax = None
        selectedPlot = None
        grid = None
    else:
        parser = argparse.ArgumentParser(description=
                                         "Plot statistics for accelerometer file")
        parser.add_argument("filename", help="Input filename")
        parser.add_argument("--controlfile", nargs="?", help="INI file to control plotting")
        parser.add_argument("--select", nargs="?", help="INI file to control plotting")
        parser.add_argument("--showtime", help="X axis is actual time", action="store_true")
        parser.add_argument("--ymin", help="Y axis minimum", type=float, default=None)
        parser.add_argument("--ymax", help="Y axis maximum", type=float, default=None)
        parser.add_argument("--grid", help="Add grid to plot", action="store_true")
        args = parser.parse_args()
        filePath = args.filename
        controlFile = args.controlfile
        showtime = args.showtime
        ymin = args.ymin
        ymax = args.ymax
        selectedPlot = args.select
        grid = args.grid

    plotMinutes = PlotMinutes()
    plotMinutes(filePath, controlFile, showtime,
                ymin, ymax, selectedPlot, grid)

if __name__ == "__main__":
    main()

