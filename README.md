# kinetics - Open Movement AX3 etc. analysis code.

AX3 accelerometers are open source accelerometer based data loggers,
see https://github.com/digitalinteraction/openmovement Several
projects I am involved in use these devices, and some also mobile
phones to collect data, which is in the same format as the CSV files
produced for AX3 data, so we can use the same tools for both.  These
are some of the tools, selected for their general usefulness.

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

### ax3_split.py

Split AX3 CSV data file into per-day files.  The command line
parameter is the CSV file, produced by cwa.py The output files have
the date of the data in them appended to the name part of the
filename.

For example:

```
python3 ax3_split.py ../myDataFile.csv
Splitting ../myDatafile.csv
Skip header line datetime, x, y, z

Output file is ..//myDataFile_2020-01-29.csv
Output file is ..//myDataFile_2020-01-30.csv
Output file is ..//myDataFile_2020-01-31.csv
Output file is ..//myDatafile_2020-01-01.csv
Output file is ..//myDataFile_2020-02-02.csv
Output file is ..//myDataFile_2020-02-03.csv
Output file is ..//myDataFile_2020-02-04.csv
Output file is ..//myDataFile_2020-02-05.csv
```

### ax3_stats.py

Generate descriptive statistics for the AX3 CSV file produced by cwa.py.  Also produces three new output files. These are:

* The CSV file with the date/time field converted to epoch and a total acceleration field added
* A CSV file with aggregated data for each minute
* A CSV file with aggregated data for each minute after the mean value for that minute has been subtracted

The first file is used as the input file to some other programs, like ax3_seconds_stats.py

For the last two files, the  fields are:

* Epoch time of this minute
* minute number (0 is first minute in file)
* number of readings in this minute
* x axis rms acceleration
* x axis peak to peak acceleration
* x axis mean acceleration
* x axis standard deviation
* y axis mean acceleration
* y axis peak to peak acceleration
* y axis rms acceleration
* y axis standard deviation
* z axis mean acceleration
* z axis peak to peak acceleration
* z axis rms acceleration
* z axis standard deviation
* total acceleration mean acceleration
* total acceleration peak to peak acceleration
* total acceleration rms acceleration
* total acceleration standard deviation
* is baselined - a flag that is 0 for non-baselined data, 1 for baselined

### ax3_median.py

Median filter for AX3 CSV data.  It takes a CSV file in the format produced by
cwa.py and applies a median filter to the x, y and z axis entries.  The resulting output file is the same as input file, but with "median" prepended to it.
e.g. fred.csv -> median_fred.csv.

The command line options are:

* `--window WINDOW`  Set the window size, which must be an odd number. Default is 7.

### ax3_plot_minutes.py

Plot minutes data, i.e. the per-minute aggregated data produced by ax3_stats.py.

```
usage: ax3_plot_minutes.py [-h] [--controlfile [CONTROLFILE]]
                           [--select [SELECT]] [--showtime] [--ymin YMIN]
                           [--ymax YMAX]
                           filename

Plot statistics for accelerometer file

positional arguments:
  filename              Input filename

optional arguments:
  -h, --help            show this help message and exit
  --controlfile [CONTROLFILE]
                        INI file to control plotting
  --grid                Add grid to plot
  --select [SELECT]     INI file to control plotting
  --showtime            X axis is actual time
  --ymin YMIN           Y axis minimum

  --ymax YMAX           Y axis maximum
  ```

### ax3_seconds_stats.py

This attempts to aggregate multiple values into ones per second to reduce the
amount of data that needs to be processed.  It produces several output files:

* file of per second means of x y and z axes
* file of per second means of x y and z axes
* file of per second means of x y and z axes with absolute values below the limit parameter on the specified axis set to zero


```
usage: ax3_seconds_stats.py [-h] [--axis AXIS] [--limit LIMIT] filename

Convert accelerometer file to per second values

positional arguments:
  filename       Input filename

optional arguments:
  -h, --help     show this help message and exit
  --axis AXIS    Axis number
  --limit LIMIT  +/- limit, default is 5 (percent)
  ```


### ax3_crunch.py

This runs a processing chain of some of the above programs on a .CWA file.  It takes one or two command line parameters. The first is the .CWA file to process
and the second is the name of an optional .ini format configuration file to obtain the settings to use in the various processing steps.  If it is not specified, then `crunch_default.ini` is used.

e.g.

`python3 ax3_crunch myfile.CWA crunch_params.ini`

or

`python3 ax3_crunch myfile.CWA`

It runs the following steps:

* cwa.py if the CSV file corresponding to the .CWA does not already exist. If
it does exist it skips this step to save time
* ax3_split.py on the resulting CSV
* For each file produced by ax3_split.py, it runs
** ax3_stats.py
** ax3_plot_minutes.py
** ax3_seconds_stats.py, by default using axis 3 for the limit checking for the "swept" file, and a limit of 0.05


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

The cutoff is the cut-off frequency for the 4th order Butterworth high pass
filter, in Hz. A value of 0.01 means 0.01 Hertz.

The command line options are:

* `--config CONFIG`  Configuration filename CONFIG, default is configuration.txt
* `--limit LIMIT`    Stop after this number of output lines
* `--verbose`        Verbose output
* `--version`        Display program version

## C++

These are the modules written in C++:

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
