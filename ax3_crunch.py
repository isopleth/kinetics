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

#
# Process one CWA file.  The file is specified on the command line:
#
# python3 ax3_crunch.py ../myDataFile.CWA
# etc.

from pathlib import Path
import argparse
import ax3_plot_minutes
import ax3_seconds_stats
import ax3_split
import ax3_stats
import configparser
import cwa
import os
import sys
import time

def get(config, section, key):
    if key in config[section]:
        return config[section][key]
    return None

def getb(config, section, key):
    """ Get boolean value from config file """
    value = get(config, section, key)
    if value is None:
        return False
    return bool(value)

def process(file, configFile):

    config = configparser.ConfigParser()
    if configFile is not None:
        if os.path.exists(configFile):
            config.read(configFile)
        else:
            print(f"Control file {configFile} not found", file=sys.stderr)
            return
        

    # .cwa -> csv
    outputFile, metadataFile = cwa.cwa(file, process=False)
    # Generate output file if it doesn't exist
    outputFilePath = Path(outputFile)
    if not outputFilePath.is_file():
        outputFile, metadataFile = cwa.cwa(file)
        print(f"Output file is {outputFile}")
        print(f"Metadata file is {metadataFile}")
    else:
        print(f"Not regenerating existing file {outputFile}")
    print()

    # Split the file
    print(f"Splitting {outputFile}")
    splitFiles = ax3_split.split(outputFile)

    for splitFile in splitFiles:
        datafile, nonBaselinedFile, baselinedFile = ax3_stats.stats(splitFile)

        plotMinutes = ax3_plot_minutes.PlotMinutes()
        for thisPlot in plotMinutes.fileTitles():
            if len(thisPlot) == 0:
                continue
            
            if getb(config, thisPlot, "ax3_plot_minutes"):


                bcontrolfile = get(config, thisPlot, "bcontrolfile")
                nbcontrolfile = get(config, thisPlot, "nbcontrolfile")

                showtime = getb(config, thisPlot, "showtime")

                grid = getb(config, thisPlot, "grid")

                ymin = get(config, thisPlot, "ymin")
                if ymin is not None:
                    ymin = float(ymin)

                ymax = get(config, thisPlot, "ymax")
                if ymax is not None:
                    ymax = float(ymax)

                # Only one config file for the baselined and nonbaselined
                # files at the moment
                plotMinutes(nonBaselinedFile, nbcontrolfile,
                            showtime, ymin, ymax, thisPlot, grid)
                plotMinutes(baselinedFile, bcontrolfile,
                            showtime, ymin, ymax, thisPlot, grid)

        if getb(config, thisPlot, "ax3_seconds_stat"):
            limit = get(config, "seconds_stat", "limit")
            if limit is not None:
                limit = float(limit)
                
            secondsMeansFile, secondsRmsFile, sweptFile = ax3_seconds_stats.process(splitFile,
                                                                                    limit=limit, axis=3)

def main():
    parser = argparse.ArgumentParser(description=
                                     "Processing chain for ax3_... scripts")
    parser.add_argument("filename", help="Input filename")
    parser.add_argument("--controlfile", nargs="?",
                        help="INI file to control plotting",
                        default="crunch_default.ini")
    args = parser.parse_args()
    filePath = args.filename
    controlFile = args.controlfile

    filePath = args.filename
    name, extension =  os.path.splitext(filePath)

    if extension == ".csv":
        print("You need the .CWA, not the .csv", file=stderr)
        os.exit(0)
            
    elapsed = time.time();
    process(filePath, controlFile)
    elapsed = time.time() - elapsed
    print(f"Elapsed time {int(round(elapsed))} seconds")

if __name__ == "__main__":
    main()
