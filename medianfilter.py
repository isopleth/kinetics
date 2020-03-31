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
# Generic median filter
#

import numpy as np

def medianFilter(inputArray, window, verboseUpdates = 0):
    """Apply median filter to an array. 
    inputArray is a 1-D array containing the input data
    window is the window size - must be odd
    verboseUpdates is the number of entries to process before emitting
    a status message.  Zero means no progress messages.
    Returns a new array containing inputArray contents with median
    filter applied """
    outputArray = np.zeros(len(inputArray), dtype=inputArray.dtype)
    halfWindow = (window - 1) // 2
    for arrayIndex in range(len(inputArray)):
        fullStartElementIndex = arrayIndex - halfWindow
        if fullStartElementIndex < 0:
            startElementIndex = 0
        else:
            startElementIndex = fullStartElementIndex

        fullEndElementIndex = arrayIndex + halfWindow
        if fullEndElementIndex > len(inputArray) - 1:
            endElementIndex = len(inputArray) - 1
        else:
            endElementIndex = fullEndElementIndex

        medianArray = np.zeros(window)
        medianArrayIndex = startElementIndex - fullStartElementIndex
        for index in range(startElementIndex, endElementIndex + 1):
            medianArray[medianArrayIndex] = inputArray[index]
            medianArrayIndex += 1

        if fullStartElementIndex != startElementIndex:
            for index in range(0, fullStartElementIndex - startElementIndex):
                medianArray[index] = inputArray[0]

        if fullEndElementIndex != endElementIndex:
            for index in range(medianArrayIndex, window):
                medianArray[index] = inputArray[-1]

        outputArray[arrayIndex] = np.median(medianArray)

        if verboseUpdates != 0 and (arrayIndex + 1) % verboseUpdates == 0:
            percent = (100 * arrayIndex) // len(inputArray)
            print(f"{arrayIndex + 1} medians " +
                  f"calculated = {percent}% of entries")
    return outputArray

def test():
    """ This test is taken from https://gist.github.com/bhawkins/3535131
    That is a different implementation of a median filter which is faster
    but uses more memory.  The AX3 data files are large, so the implementation
    above is slower but uses much less memory for large datasets. The reason
    for copying the test is to demonstrate that the two implementations
    produce identical results. """

    import matplotlib.pyplot as p
    array = np.linspace(0, 1, 101)
    array[3::10] = 1.5
    p.plot(array)
    p.plot(medianFilter(array, 3))
    p.plot(medianFilter(array, 5))
    p.show()


if __name__ == '__main__':
    test ()
    
