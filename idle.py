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
# Remove idle portions from CSV accelerometer file
#
import argparse
import sys

class Row:

    """ Represents a row from the input file
    """
    
    def __init__(self, line):

        """ Constructor - strictly speaking initializer
        """

        self.skip = False
        self.epoch = None
        self.timestamp = None

        self.fields = line.split(",")
        if len(self.fields) != 10:
            print(f"Ignore {line}, {len(fields)} fields", file=sys.stderr)
            self.skip = True
            return
            
        self.epoch = self.fields[1].strip()
        self.filteredRms = self.fields[9].strip()
        try:
            self.filteredRms = float(self.filteredRms)
            self.epoch = float(self.epoch)
        except ValueError:
            print(f"Conversion error, ignore {line}", file=sys.stderr)
            self.skip = True

    def isIdle(self):
        return self.filteredRms < 0.1

class Processor:

    def __init__(self, filename):
        idleThreshold = 1200
        isIdle = False
        startIdleTime = None
        idleTime = 0
        with open(filename, "r") as self.fh:
            line = self.fh.readline()
            while line:
                row = Row(line)
                if row.isIdle():
                    if isIdle:
                        idleTime = row.epoch - startIdleTime
                    else:
                        isIdle = True
                        startIdleTime = row.epoch
                else:
                    if isIdle:
                        # Change from idle to not idle
                        if idleTime > idleThreshold:
                            print(f"Idle at {startIdleTime} to {row.epoch}, idle time {idleTime}")
                            isIdle = False
                line = self.fh.readline()

def main():
    if len(sys.argv) < 2:
        root = tk.Tk()
        root.withdraw()
        filePath = filedialog.askopenfilename(
            filetypes = [("Comma separated file (CSV) format",".csv")])
    else:
        parser = argparse.ArgumentParser(description=
                                         "Split accerometer file")
        parser.add_argument("filename", help="Input filename")
        args = parser.parse_args()
        filePath = args.filename

    processor = Processor(filePath)

if __name__ == "__main__":
    main()
  
