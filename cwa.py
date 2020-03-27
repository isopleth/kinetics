#!/usr/bin/env python3
# coding=UTF-8
#
#  CWA Data Conversion Tool
#     
#  Copyright (c) 2011 Technische Universität München, 
#  Distributed Multimodal Information Processing Group
#  http://vmi.lmt.ei.tum.de
#  All rights reserved.
#
#  Stefan Diewald <stefan.diewald [at] tum.de>
#     
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions
#  are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of the University or Institute nor the names
#    of its contributors may be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
#  FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
#  COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
#  INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
#  BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
#  ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#  POSSIBILITY OF SUCH DAMAGE.
#

# The program is used to convert Axivity AX3 accelerometer data files,
# CWA-DATA.CWA to comma separated variable text file format.
#
# The original program was modified by Jason Leake, November 2019, as follows:
#
# - Convert to Python3
# - Open dialog box to get the input filename if not specified on command line
# - Output to an ascii file instead of an Sqlite database
# - Output annotations to another file, <original_file>_metadata.txt
# - Add some more annotation abbreviations
# - Don't print a * for every record converted, just a summary occasionally
# - Some re-arrangement of the code
# - Add cwa function to make trivially callable from other Python modules
#

from datetime import datetime
from math import floor
from os import path
from struct import pack, unpack
from tkinter import filedialog
import argparse
import io
import sys
import time
import tkinter as tk

def byte(value):
    return (value + 2 ** 7) % 2 ** 8 - 2 ** 7 

def ushort(value):
    return value % 2 ** 16

def short(value):
    return (value + 2 ** 15) % 2 ** 16 - 2 ** 15

# Local "URL-decode as UTF-8 string" function
def urldecode(input):
    output = bytearray()
    nibbles = 0
    value = 0
    # Each input character
    for char in input:
        if char == '%':
            # Begin a percent-encoded hex pair
            nibbles = 2
            value = 0
        elif nibbles > 0:
            # Parse the percent-encoded hex digits
            value *= 16
            if char >= 'a' and char <= 'f':
                value += ord(char) + 10 - ord('a')
            elif char >= 'A' and char <= 'F':
                value += ord(char) + 10 - ord('A')
            elif char >= '0' and char <= '9':
                value += ord(char) - ord('0')
            nibbles -= 1
            if nibbles == 0:
                output.append(value)
        elif char == '+':
            # Treat plus as space (application/x-www-form-urlencoded)
            output.append(ord(' '))
        else:
            # Preserve character
            output.append(ord(char))
    return output.decode('utf-8')

class Parameters:
    """ Holds parameters derived from command line options etc
    """

    def __init__(self, args=None):
        if args is not None:
            self.verbose = args.verbose
            self.limit = args.limit
            self.version = args.version
            self.linux = args.linux
            self.standardGravity = args.sg
            self.writeHeader = not args.noheader
        else:
            self.verbose = False
            self.limit = None
            self.version = False
            self.linux = False
            self.standardGravity = False
            self.writeHeader = True

    def set(self, verbose, limit, version, linux, sg, noheader):
        """ Set parameters to non-default values """
        self.verbose = verbose
        self.limit = limit
        self.version = version
        self.linux = linux
        self.standardGravity = sg
        self.writeHeader = not noheader 

class CWA_Sample:
    pass

class CWA:

    # Placeholder in case we want to understand data produced by
    # devices other than AX3
    isAnAx3 = True
    STANDARD_GRAVITY = 9.80665 # m/s^2, i.e. 58966 furlongs/fortnight^2
    
    def __init__(self, filename):
        """ Parameters: filename - input filename
        """
        self._filename = filename
        self.outputFilename = path.splitext(self._filename)[0] + ".csv"
        self.metadataFilename = path.splitext(self._filename)[0] + "_metadata.txt"

    def __call__(self, parameters):

        if parameters.linux:
            lineEnd = "\n"
        else:
            lineEnd = "\r\n"
            
        if parameters.version:
            # My versions contain my github username to avoid
            # clashes, in case OpenMovement start producing their
            # own version numbering scheme
            print("cwa.py, version Isopleth 1.03")

        linesGenerated = 0
        if len(self._filename) == 0:
            print("No filename specified", file=sys.stderr)
            return linesGenerated

        print(f"Converting {self._filename}, output is "
              f"{self.outputFilename} and {self.metadataFilename}")
        if not path.exists(self._filename):
            print("File does not exist", file=sys.stderr)
            return linesGenerated

        lastSequenceId = None
        lastTimestampOffset = None
        lastTimestamp = None

        with open(self.outputFilename, 'w') as out:
            if parameters.writeHeader:
                out.write("datetime, x, y, z{}".format(lineEnd))
            
            with open(self._filename, 'rb') as self.fh:
                header = self.fh.read(2).decode("ISO-8859-1")
                while len(header) == 2:
                    if parameters.verbose:
                        print("Section header is %s" % (header))

                    if header == 'MD':
                        self.parse_header(metadataFilename=self.metadataFilename)
                    elif header == 'UB':
                        blockSize = unpack('H', self.fh.read(2))[0]
                    elif header == 'SI':
                        pass
                    elif header == 'AX':
                        packetLength = unpack('H', self.fh.read(2))[0]               
                        deviceId = unpack('H', self.fh.read(2))[0]
                        sessionId = unpack('I', self.fh.read(4))[0]
                        sequenceId = unpack('I', self.fh.read(4))[0]
                        sampleTime = self.read_timestamp(self.fh.read(4))
                        light = unpack('H', self.fh.read(2))[0]
                        temperature = unpack('H', self.fh.read(2))[0]
                        events = self.fh.read(1)
                        battery = unpack('B', self.fh.read(1))[0]
                        sampleRate = unpack('B', self.fh.read(1))[0]
                        numAxesBPS = unpack('B', self.fh.read(1))[0]
                        timestampOffset = unpack('h', self.fh.read(2))[0]
                        sampleCount = unpack('H', self.fh.read(2))[0]
                        if parameters.verbose:
                            print(f"Sample count is {sampleCount}")
                        
                        sampleData = io.BytesIO(self.fh.read(480))
                        checksum = unpack('H', self.fh.read(2))[0]
                        
                        if packetLength != 508:
                            print("Packet length is not 508!", file=sys.stderr)
                            continue
                        
                        if sampleTime == None:
                            print("Sample time is undefined!", file=sys.stderr)
                            continue
                        
                        if sampleRate == 0:
                            chksum = 0
                        else:
                            # rewind for checksum calculation
                            self.fh.seek(-packetLength - 4, 1)
                            # calculate checksum
                            chksum = 0
                            for x in range(packetLength // 2 + 2):
                                chksum += unpack('H', self.fh.read(2))[0]
                            chksum %= 2 ** 16
                        
                        if chksum != 0:
                            continue
                        
                        if sessionId != self.sessionId:
                            print(f"Bad session ID {sessionId} - should be {self.sessionId}", file=sys.stderr)
                            continue
                        
                        if ((numAxesBPS >> 4) & 15) != 3:
                            print('[ERROR: Axes!=3 not supported yet -- this will not work properly]', file=sys.stderr)

                        if (light & 0xfc00) != 0:
                            print('[ERROR: Scale not supported yet -- this will not work properly]', file=sys.stderr)
                            
                        if (numAxesBPS & 15) == 2:
                            bps = 6
                        elif (numAxesBPS & 15) == 0:
                            bps = 4
                        
                        freq = float(3200) / (1 << (15 - sampleRate & 15))
                        if freq <= 0:
                            freq = 1
                        
                        # range = 16 >> (rateCode >> 6)
                        
                        timeFractional = 0                    
                        # if top-bit set, we have a fractional date
                        if deviceId & 0x8000:
                            # Need to undo backwards-compatible shim
                            # by calculating how many whole samples
                            # the fractional part of timestamp
                            # accounts for.
                            timeFractional = (deviceId & 0x7fff) * 2     # use original deviceId field bottom 15-bits as 16-bit fractional time
                            timestampOffset += (timeFractional * int(freq)) // 65536 # undo the backwards-compatible shift (as we have a true fractional)
                            timeFractional = float(timeFractional) / 65536
                        
                        # Add fractional time to timestamp
                        timestamp = float(time.mktime(sampleTime)) + timeFractional
                        
                        # --- Time interpolation ---
                        # Reset interpolator if there's a sequence break or there was no previous timestamp
                        if lastSequenceId == None or (lastSequenceId + 1) & 0xffff != sequenceId or lastTimestampOffset == None or lastTimestamp == None:
                            # Bootstrapping condition is a sample one second ago (assuming the ideal frequency)
                            lastTimestampOffset = timestampOffset - freq
                            lastTimestamp = timestamp - 1
                            lastSequenceId = sequenceId - 1
                        
                        localFreq = float(timestampOffset - lastTimestampOffset) / (timestamp - lastTimestamp)
                        time0 = timestamp + -timestampOffset / localFreq
                        
                        # Update for next loop
                        lastSequenceId = sequenceId
                        lastTimestampOffset = timestampOffset - sampleCount
                        lastTimestamp = timestamp
                        
                        for x in range(sampleCount):
                            sample = CWA_Sample()
                            if bps == 6:
                                sample.x = unpack('h', sampleData.read(2))[0]
                                sample.y = unpack('h', sampleData.read(2))[0]
                                sample.z = unpack('h', sampleData.read(2))[0]
                            elif bps == 4:
                                temp = unpack('I', sampleData.read(4))[0]
                                temp2 = (6 - byte(temp >> 30))
                                sample.x = short(short((ushort(65472) & ushort(temp << 6))) >> temp2)
                                sample.y = short(short((ushort(65472) & ushort(temp >> 4))) >> temp2)
                                sample.z = short(short((ushort(65472) & ushort(temp >> 14))) >> temp2)
                            
                            sample.t = time0 + (x / localFreq)
                            tStr = "{:.5f}".format(sample.t)

                            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(int(floor(sample.t))))
                            fractionTimestamp = tStr.split(".",1)[1]

                            # Convert 10 us units to ms units
                            fractionTimestamp = float(fractionTimestamp) / 100
                            # Integer number of ms
                            fractionTimestamp = int(fractionTimestamp)
                            fractionTimestamp = str(fractionTimestamp)
                            # Pad to three digits.  It is after decimal point so add
                            # digits to left. e.g. if it is 10 ms, then this would
                            # be represented as 010 after the decimal point, i.e.
                            # 0.010
                            while len(fractionTimestamp) < 3:
                                fractionTimestamp = "0" + fractionTimestamp
                            # Units for AX3 are 1/256 g
                            # Standard gravity is 9.80665
                            outvals = [sample.x, sample.y, sample.z]
                            if self.isAnAx3:
                                if parameters.standardGravity:
                                    conversionFactor = self.STANDARD_GRAVITY / 256
                                else:
                                    conversionFactor = 1/256;
                                for index in range(len(outvals)):
                                    outvals[index] = outvals[index] * conversionFactor
                            out.write("{}.{},{:.06f},{:.06f},{:.06f}{}".format(
                                timestamp, fractionTimestamp, outvals[0],
                                outvals[1], outvals[2], lineEnd))
                                    
                            linesGenerated += 1

                            if parameters.limit is not None and linesGenerated >= parameters.limit:
                                return linesGenerated
                            
                            if linesGenerated % 1000000 == 0 and linesGenerated != 0:
                                print(f"{linesGenerated} lines of output generated")
                    else:
                        print(f"Unrecognized section header, {header}!", file=sys.stderr)
                        break
                    header = self.fh.read(2).decode("ISO-8859-1")
                
        return linesGenerated

    # Parse the "MD" format file header
    def parse_header(self, metadataFilename = None):
        blockSize = unpack('H', self.fh.read(2))[0]
        performClear = unpack('B', self.fh.read(1))[0]
        deviceId = unpack('H', self.fh.read(2))[0]
        sessionId = unpack('I', self.fh.read(4))[0]
        deviceIdUpper = unpack('H', self.fh.read(2))[0]
        if deviceIdUpper != 0xffff:
            deviceId |= deviceIdUpper << 16
        loggingStartTime = self.fh.read(4)
        loggingEndTime = self.fh.read(4)
        loggingCapacity = unpack('I', self.fh.read(4))[0]
        allowStandby = unpack('B', self.fh.read(1))[0]
        debuggingInfo = unpack('B', self.fh.read(1))[0]
        batteryMinimumToLog = unpack('H', self.fh.read(2))[0]
        batteryWarning = unpack('H', self.fh.read(2))[0]
        enableSerial = unpack('B', self.fh.read(1))[0]
        lastClearTime = self.fh.read(4)
        samplingRate = unpack('B', self.fh.read(1))[0]
        lastChangeTime = self.fh.read(4)
        firmwareVersion = unpack('B', self.fh.read(1))[0]

        reserved = self.fh.read(22)

        annotationBlock = self.fh.read(448 + 512)
        
        if len(annotationBlock) < 448 + 512:
            annotationBlock = ""

        annotation = ""
        for x in annotationBlock:
            if x != 255 and x != ' ':
                if x == '?':
                    x = '&'
                annotation += str(chr(x))
        annotation = annotation.strip()

        annotationElements = annotation.split('&')
        annotationNames = {
                # at device set-up time
                "_c": "studyCentre",
                "_s": "studyCode",
                "_i": "investigator",
                "_x": "exerciseCode",
                "_v": "volunteerNum",
                "_p": "bodyLocation",
                "_so": "setupOperator",
                "_n": "notes",
                "_se": "sex",
                "_h": "height",
                "_w": "weight",
                "_ha": "handedness",
                "_sc": "subject code",
                # at retrieval time
                "_b": "startTime", 
                "_e": "endTime", 
                "_ro": "recoveryOperator", 
                "_r": "retrievalTime", 
                "_co": "comments"}
        annotations = dict()
        for element in annotationElements:
            kv = element.split('=', 2)
            annotationName = urldecode(kv[0])
            if kv[0] in annotationNames:
                annotationName = annotationNames[kv[0]]
                annotations[annotationName] = urldecode(kv[1])

        for x in ('startTime', 'endTime', 'retrievalTime'):
            if x in annotations:
                if '/' in annotations[x]:
                    annotations[x] = time.strptime(annotations[x], '%d/%m/%Y')
                else:
                    annotations[x] = time.strptime(annotations[x], '%Y-%m-%d %H:%M:%S')

        self.annotations = annotations
        self.deviceId = deviceId
        self.sessionId = sessionId
        self.lastClearTime = self.read_timestamp(lastClearTime)
        self.lastChangeTime = self.read_timestamp(lastChangeTime)
        self.firmwareVersion = firmwareVersion if firmwareVersion != 255 else 0
        self.loggingStartTime = self.read_timestamp(loggingStartTime)
        self.loggingEndTime = self.read_timestamp(loggingEndTime)

        if metadataFilename is not None:
            with open(metadataFilename, "w") as out:
                out.write(f"Device ID: {self.deviceId}\n")
                out.write(f"Session ID: {self.sessionId}\n")
                out.write(f"Last clear time: {self.lastClearTime}\n")
                out.write(f"Last change time: {self.lastChangeTime}\n")
                out.write(f"Logging start time: {self.loggingStartTime}\n")
                out.write(f"Logging end time: {self.loggingEndTime}\n")
                out.write(f"Firmware version: {self.firmwareVersion}\n")
                out.write("Annotations\n")
                for key in self.annotations.keys():
                    out.write(f"{key}: {self.annotations.get(key)}\n")
        
    def read_timestamp(self, stamp):
        stamp = unpack('I', stamp)[0]
        # bit pattern:  YYYYYYMM MMDDDDDh hhhhmmmm mmssssss
        year  = ((stamp >> 26) & 0x3f) + 2000
        month = (stamp >> 22) & 0x0f
        day   = (stamp >> 17) & 0x1f
        hours = (stamp >> 12) & 0x1f
        mins  = (stamp >>  6) & 0x3f
        secs  = (stamp >>  0) & 0x3f
        try:
            t = time.strptime(str(datetime(year,
                                           month,
                                           day,
                                           hours,
                                           mins,
                                           secs)), '%Y-%m-%d %H:%M:%S')
        except ValueError:
            t = None
        return t
    
def main():
    
    if len(sys.argv) < 2:
        root = tk.Tk()
        root.withdraw()
        filePath = filedialog.askopenfilename(
            filetypes = [("Continuous Wave Accelerometer (CWA) format",".CWA")])
        parameters = Parameters()
    else:
        parser = argparse.ArgumentParser(description="Convert Continuous Wave Accelerometer format files to CSV")
        parser.add_argument("filename",
                            help="Input filename")
        parser.add_argument("--noheader",
                            help="Suppress headings on columns",
                            action = "store_true")
        parser.add_argument("--verbose",
                            help="Verbose output", action="store_true")
        parser.add_argument("--limit",
                            help="Stop after this number of output lines",
                            type=int)
        parser.add_argument("--version",
                            help="Display program version", action="store_true")
        parser.add_argument("--linux",
                            help="Output Linux line endings",
                            action="store_true")
        parser.add_argument("--sg",
                            help="Use standard gravity for units",
                            action="store_true")

        args = parser.parse_args()
        parameters = Parameters(args)
        filePath = args.filename

    cwa = CWA(filePath)
    linesGenerated = cwa(parameters)
    print(f"{linesGenerated} lines of output generated")

def cwa(filePath, verbose=False, limit=None, version=False,
        linux=False, sg=False, noheader=False, process=True):
    """ This is an easy to use entry point for other modules
    """
    cwa = CWA(filePath)
    parameters = Parameters()
    parameters.set(verbose, limit, version, linux, sg, noheader)
    if process:
        linesGenerated = cwa(parameters)
        print(f"{linesGenerated} lines of output generated")
    return [ cwa.outputFilename, cwa.metadataFilename ]
    
if __name__ == "__main__":
    main()
