import array
from decimal import Decimal
import sys
from math import sqrt
import time

class Row:
    """ Represents a row from the input file
    """
    
    def __init__(self, line):
        """ Initializer
        """
        # True if this row is to be skipped because it contains a syntax
        # error etc
        self.skip = False
        self._epoch = None
        self._totalAcc = None
        self.timestamp = None

        line = line.strip()
        fields = line.split(",")
        if len(fields) != 4:
            print(f"Ignore {line}, {len(fields)} fields", file=sys.stderr)
            self.skip = True
            return

        if fields[0] == "datetime":
            print(f"Skip header line {line}", file=sys.stderr)
            self.skip = True
            return
            
        self.timestamp = fields[0].strip()
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
