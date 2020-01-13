# kinetics - Open Movement AX3 etc. analysis code.

These are open source accelerometer based data loggers, see
https://github.com/digitalinteraction/openmovement My project uses
these, and also mobile phones to collect data, which is in the same
format as the CSV files produced for AX3 data, so we can use the same
tools for both.  These are some of the tools, selected for their
general usefulness.

The format for the CSV files is either the AX3 type format:

`<datetime>,<val>,<val>,<val>,...`

for AX3 input files

or

`<datetime>,<epoch>,<val>,<val>,<val>,...`

for phone data or the general format of the files being processed by most of the tools.
Headers are usually generated, and may optionally be present on input files

`datetime, epoch, latitude, longitude, altitude, accuracy, speed`

`2019-07-22 13:53:58.036,1563803638, 53.23333,-2.3,77,8.224,0`

## Python

### cwa.py

Convert Continuous Wave Accelerometer format files (.CWA) to CSV.
Modified version of the Python3 script from OpenMovement.  This writes its
output to an output file instead of an SQLite database.  If the input file
is not named on the command line, then it opens a dialogue window to get it.

* `--verbose`
* `--limit LIMIT` stop after outputting LIMIT lines, good for testing
* `--version` display program version information
* `--linux` output Linux line endings instead of MSDOS ones
* `--sg` use units of standard gravity instead of g. (i.e. make 9.81 = 1 unit)

Output format is as close to OpenMovement omgui as I can make it.

At the moment there is an unexplained offset of about 1 millisecond
between the timestamps produced by OpenMovement omgui Windows program
and this script, possibly a change in the timestamp format that has
not been carried through the original OpenMovement cwa.py script.

Output format is:
`<datetime>,<x>,<y>,<z>`

Output files for `<input_file>.CWA` are `<input_file>.csv` and
`<input_file>_metadata.csv`, the latter containing the metadata read
from the CWA file.

### average.py

Reduce the CSV file by taking the means of all x, y, and z values within small
time intervals.  Adds extra columns in the output file, which are the epoch
time corresponding to the timestamp.

`<datetime>,<epoch>,<averaged x>,<averaged y>,<averaged z>,<rms>`

A further four columns are added, which are the result of a high pass
filter applied to the <averaged x>,<averaged y>,<averaged z>,<rms>.
This is a bit experimental, as earlier work I did used a high pass
filter applied to the raw values before the averages were taken and I
am still looking at whether this change is good.  The reason for it is
to avoid the huge amount of memory required to run a filter down the
original dataset, consequently allowing this program to be written in
Python instead of C++ with STXXL, for enhanced portability.

It reads a file called configuration.txt that contains some run-time
settings.  At the moment these are:

`resolution: 1
cutoff: 0.01`

The resolution is the number of decimal places in the epoch time to average
values over.  1 means 0.1 second resolution, 10 would be 0.01 etc.  It is
a bit clunky and we'll improve it later.

cutoff is the cut-off frequency for the 4th order Butterworth high pass
filter, in Hz. A value of 0.01 means 0.01 Hertz.

The command line options are:

* `--config CONFIG`  Configuration filename CONFIG, default is configuration.txt
* `--limit LIMIT`    Stop after this number of output lines
* `--verbose`        Verbose output
* `--version`        Display program version

## C++

### cleaner

This is a C++ program, originally written for processing sensor data
from mobile phones as well as AX3 data. It works in a similar way to
Average.py, by producing mean values, and RMS, over intervals.  At the
moment, this is fixed at a second from the application that the
program was originally written for, and for AX3 accelerometers
configured to store 100 samples per second.

It also runs a high pass filter across the data, this time unlike
average.py before the averaging has been done, and also computes RMS
of the filtered values, again before the averaging has been done.
Because the rtf_filter functions that it uses take a vector it has to
use Stxxl library to store all of the rows read from the file so that
it can generate the full vector.

`cleaner [options] <infile> <outfile> [type]`

`<outfile>` is the output file. It defaults to being the same as the
input file except with `_clean` appended to the stem. e.g. fred.csv
would produce fred_clean.csv.

`[type]` is the file data type, one of: gyroscope, accelerometer, ax3, location
or gpslocation. It defaults to `ax3`

Gyro, accelerometer and ax3 data have the record format:
`<datetime>,<x>,<y>,<z>`

location and gpslocation data have the record format:
`<datetime>,<latitude>,<longitude>,<altitude>,<accuracy>,<speed>`


The options are:
`-c <Hz>` or `--cutoff <Hz>` says that the HP filter cutoff frequency should be <Hz>
`-f` or `--force` causes output file to be regenerated if already exists
`-s <rate>` or `--samplerate <rate>` says that the sample rate is <rate>
e.g. `cleaner data.csv data-out.csv ax3`

The default options are `-c 0.05` and the sample rate determined from the data file

### day_splitter

Splits AX3 and similar .csv files into one file per day. It assumes
that the first field is the datetime field.

### bounding_box

Remove all geographic locations from data files outside of a geographical
bounding box.

### extract_phone

Extract various data fields from phone data files.  We use the same
format for data collected by Android phones as the OpenMovement AX3
CSV files.

### trim

Remove data from AX3 files where there was little or no movement for
a specified period. Still under development!
