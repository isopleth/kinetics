#!/usr/bin/env python3
# coding=UTF-8
#
# BSD 2-Clause License
#
# Copyright (c) 2020, Jason Leake
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
# This is a small library for processing row data
#
import array
from decimal import Decimal
import sys
from math import sqrt
import time

class Row:
    """ Represents a row from the input file
    """

    def __init__(self, line, verbose=True, decode=True):
        """Initializer.  line is the line read from the AX3 CSV file.
        verbose is True to output information messages.  decode is
        false if the numeric values should not be decoded.  You don't
        normally want to skip decoding them except when the date/time
        field only is to be extracted.

        """
        # True if this row is to be skipped because it contains a syntax
        # error etc
        self.skip = False
        self._epoch = None
        self._totalAcc = None
        self.timestamp = None
        self.date = None
        self.time = None
        self.rawLine = line

        if line.startswith("datetime"):
            if verbose:
                print(f"Skip header line {line}", file=sys.stderr)
            self.skip = True
            return

        if line.count(",") != 3:             
            print(f"Ignore {line}", file=sys.stderr)
            self.skip = True
            return

        # Only decode line if it is actually going to be processed by the
        # caller
        if decode:
            line = line.strip()
            fields = line.split(",")
            if len(fields) != 4:
                print(f"Ignore {line}, {len(fields)} fields", file=sys.stderr)
                self.skip = True
                return

            self.timestamp = fields[0].strip()
            self.date, self.time, *rest = self.timestamp.split(" ", 1)
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
