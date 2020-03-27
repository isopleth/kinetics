#!/usr/bin/env python3

#
# Process one CWA file.  The file is specified on the command line:
#
# python3 ax3_crunch.py ../myDataFile.CWA
# etc.

from pathlib import Path
import ax3_plot_minutes
import ax3_seconds_stats
import ax3_split
import ax3_stats
import cwa
import sys
import timeit

def process(file):
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
        plotMinutes(nonBaselinedFile, None, True, None, None, None, True)
        plotMinutes(baselinedFile, None, True, None, None, None, True)
        secondsMeansFile, secondsRmsFile, sweptFile = ax3_seconds_stats.process(splitFile)
        
if len(sys.argv) != 2:
    raise ValueError('No .CWA file to process specified')
elapsed = timeit.timeit(process(sys.argv[1]))
print(f"Elapsed tile {elapsed}")

