#!/usr/bin/env python3

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
import timeit

def get(config, section, key):
    if key in config[section]:
        return config[section][key]
    return None

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

        # Get the file titles from ax3_plot_minutes.py directly, later
        plotType = [ "mean_x",
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

        # Make sure that there are defaults


        for thisPlot in plotType:
            plotMinutes = ax3_plot_minutes.PlotMinutes()

            configSection = config[thisPlot]
            # Defaults if not specified, even in DEFAULT section

            bcontrolfile = get(config, thisPlot, "bcontrolfile")
            nbcontrolfile = get(config, thisPlot, "nbcontrolfile")

            showtime = get(config, thisPlot, "showtime")
            if showtime is not None:
                showtime = bool(showtime)

            grid = get(config, thisPlot, "grid")
            if grid is not None:
                grid = bool(grid)

            ymin = get(config, thisPlot, "ymin")
            if ymin is not None:
                    ymin = float(ymin)

            ymax = get(config, thisPlot, "ymax")
            if ymax is not None:
                ymax = float(ymax)

            text = get(config, thisPlot, "text")
            # Only one config file for the baselined and nonbaselined files at the moment
            plotMinutes(nonBaselinedFile, nbcontrolfile,
                        showtime, ymin, ymax, thisPlot, grid)
            plotMinutes(baselinedFile, bcontrolfile,
                        showtime, ymin, ymax, thisPlot, grid)

        axes = ["seconds_x", "seconds_y", "seconds_z", "seconds_total"]
        for axis in range(len(axes)):
            limit = get(config, axes[axis], "limit")
            if limit is not None:
                limit = float(limit)
                
            secondsMeansFile, secondsRmsFile, sweptFile = ax3_seconds_stats.process(splitFile,
                                                                                    limit=limit, axis=axis)

def main():
    parser = argparse.ArgumentParser(description=
                                     "Processing chain for ax3_... scripts")
    parser.add_argument("filename", help="Input filename")
    parser.add_argument("--controlfile", nargs="?", help="INI file to control plotting", default="crunch_default.ini")
    args = parser.parse_args()
    filePath = args.filename
    controlFile = args.controlfile

    filePath = args.filename
    name, extension =  os.path.splitext(filePath)

    if extension == ".csv":
        print("You need the .CWA, not the .csv", file=stderr)
        os.exit(0)
            
    elapsed = timeit.timeit(process(filePath, controlFile))
    print(f"Elapsed tile {elapsed}")
        
if __name__ == "__main__":
    main()
