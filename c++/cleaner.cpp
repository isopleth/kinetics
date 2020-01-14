// BSD 2-Clause License
//
// Copyright (c) 2019, Jason Leake
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
// 1. Redistributions of source code must retain the above copyright notice, this
//    list of conditions and the following disclaimer.
//
// 2. Redistributions in binary form must reproduce the above copyright notice,
//    this list of conditions and the following disclaimer in the documentation
//    and/or other materials provided with the distribution.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
// AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
// IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
// DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
// FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
// DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
// SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
// CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
// OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
// OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//

/**
 * Clean up AX3 and phone CSV datasets, mainly by aggregating data
 * into longer rtime periods.
 *
 * Jason Leake October 2019
 */

#include "Mean.h"
#include "Option.h"
#include "Row.h"
#include "Rows.h"
#include "cleaner_files/Parameters.h"
#include "cleaner_files/Reduce.h"
#include "util.h"
#include <chrono>
#include <cmath>
#include <deque>
#include <execinfo.h>
#include <fstream>
#include <iostream>
#include <iterator>
#include <libfccp/csv.h>
#include <list>
#include <rtf_common.h>
#include <signal.h>
#include <stxxl/bits/common/external_shared_ptr.h>
#include <stxxl/vector>
#include <unistd.h>

using namespace std;
using namespace cleaner;
namespace fs = std::filesystem;

static constexpr auto DEBUG = false;
static auto progname = "cleaner";

/**
 * Convert axis index to axis name
 *
 * @param axisNumber axis number
 * @return corresponding axis name string
 */
static auto axisNumberToName(int axisNumber) -> string {
  const string name[] = {"x","y","z","?"};
  if (axisNumber >= 3 || axisNumber < 0) {
    return name[3];
  }
  return name[axisNumber];
}

/**
 * Baseline the data using high pass filter
 *
 * @param parameters run-time parameters
 * @param rows accelerometer readings
 * @param from data type of input rows, i.e. what sort of reading
 * @param to data type of desired output rows, i.e. what sort of reading
 */
static auto baseline(const cleaner::Parameters& parameters,
		     Rows& rows,
		     Row::DataType from,
		     Row::DataType to) -> void {
  cout << "High pass filter to remove baseline and slow drift" << endl; 
  auto inData = vector<double>{};
  auto outData = vector<double>{};
  for (auto axis = 0; axis < 3; axis++) {
    cout << axisNumberToName(axis) << " axis filter:" << endl;
    inData.clear();
    outData.clear();
    cout << "Reserve " << rows.size() << " rows in vector" << endl;
    inData.reserve(rows.size());
    outData.resize(rows.size());
    for (auto index = size_t{0}; index < rows.size(); index++) {
      inData.push_back(rows.getValue(index, from, axis));
    }

    auto sampleRate = parameters.getSampleRate(); // Sample rate
    auto cutoff = parameters.getCutoff();     // Cutoff in Hertz.
    cout << "Cutoff is " << cutoff << " Hz\n";
    auto theFilter = rtf_create_butterworth(1,
					    RTF_DOUBLE,
					    cutoff/sampleRate,
					    4,  // 
					    1); // High pass

    cout << "Run filter" << endl;
    rtf_filter(theFilter, inData.data(), outData.data(), inData.size());
    cout << "Filter completed\n" << endl;

    rtf_destroy_filter(theFilter);
    theFilter = nullptr;
    
    // Outputting baselined data
    for (auto index = size_t{0}; index < rows.size(); index++) {
      rows.putValue(index, to, axis, outData.at(index));
    }
  }
}

/**
 * Estimate the sample rate
 *
 * @params rows data from the file
 * @param sampleRateFilename file to write sample rate info to
 * @return estimated sample rate
 */
static auto getSampleRate(const Rows& rows,
			  const std::string& sampleRateFilename) {

  auto oldSecond = 0ul;
  auto samplesInCurrentSecond = 0ul;
  auto first = true;
  auto binSizes = map<int, int>();
  for (auto rowIndex = size_t{0}; rowIndex < rows.size(); rowIndex++) {
    auto lsecond = rows.getSecond(rowIndex);
    // Check if we have moved on to a new second
    if (lsecond != oldSecond) {
      oldSecond = lsecond;
      if (first) {
	// First value processed in run.  Nothing to see here.
	first = false;
      } else {
	auto it = binSizes.find(samplesInCurrentSecond);
	if (it != binSizes.end()) {
	  it->second++;
	}
	else {
	  binSizes.insert({samplesInCurrentSecond,1});
	}
	samplesInCurrentSecond = 0;
      }
    }
    samplesInCurrentSecond++;
  }

  cout << "Log sample rate info to " << sampleRateFilename << endl;
  auto sampleRateFile = ofstream{sampleRateFilename};
  
  auto meanSampleRate = Mean{};
  for (const auto& it: binSizes) {
    auto outputLine = stringstream{};
    outputLine << "Seconds with "
	       << it.first
	       << " samples in them = "
	       << it.second;
    cout << outputLine.str() << endl;
    
    sampleRateFile << outputLine.str() << endl;

    meanSampleRate.addMultiple(it.first, it.second);
  }
  sampleRateFile.close();
  
  if (!meanSampleRate.getCount()) {
    cout << "No sample rate because no samples" << endl;
    return 0.0;
  }
  
  cout << "Mean sample rate is " << meanSampleRate.getAverage() <<
    " samples per second" << endl;
  return meanSampleRate.getAverage();
}


/**
 * Process an accelerometer or gyro data file, by reading it and appending
 * it to the Rows object.
 *
 * @param rows rows to append records to
 * @infilename filename containing data, see in.set_header() call below
 * @return number of lines read
 */
static auto processKinematic(Rows& rows,
			     const filesystem::path& infilename) {

  auto hasHeader = util::csvHasHeader(infilename, true);
  
  auto in = io::CSVReader<4>{infilename};
  in.set_header("datetime", "x", "y", "z");

  auto inCount = 0ul;

  auto datetime = string{};
  auto x = 0.;
  auto y = 0.;
  auto z = 0.;

  if (hasHeader) {
    in.read_header(io::ignore_missing_column, "datetime", "x", "y", "z");
  }
  
  while (true) {    
    if (!in.read_row(datetime, x, y, z)) {
      break;
    }

    inCount++;
    if (inCount % 100000 == 0) {
      cout << inCount << " lines read\r";
      cout.flush();
    }
    rows.push_back(datetime, x, y, z);
  }
  
  return inCount;
}


/**
 * Process location data, by reading it and appending to the Rows object.
 *<
 * @param rows rows to append records to
 * @infilename filename containing data, see in.set_header() call below
 * @return number of lines read
 */

static auto processLocation(Rows& rows, const filesystem::path& infilename) {
  auto hasHeader = util::csvHasHeader(infilename, true);
  auto in = io::CSVReader<6>{infilename};
  in.set_header("datetime", "latitude", "longitude",
		"altitude", "accuracy", "speed");

  auto inCount = 0ul;

  auto datetime = string{};
  auto latitude = 0.;
  auto longitude = 0.;
  auto altitude = 0.;
  auto accuracy = 0.;
  auto speed = 0.;

  if (hasHeader) {
    in.read_header(io::ignore_missing_column, "datetime", "latitude", "longitude",
		   "altitude", "accuracy", "speed");
  }
  
  while (true) {
    if (!in.read_row(datetime, latitude, longitude,
		     altitude, accuracy, speed)) {
      break;
    }

    inCount++;
    if (inCount % 100000 == 0) {
      cout << inCount << " lines read\r";
      cout.flush();
    }
    rows.push_back(datetime, latitude, longitude, altitude, accuracy, speed);
  }
  return inCount;
}

/**
 * Main processing method.  Processes a single input file and produces
 * a single output file from it.
 *
 * @param infilename input filename
 * @param outFilename output filename
 * @param parameters run-time parameters setting. May be updated.
 */
static auto process(const filesystem::path& infilename,
		    const filesystem::path& outFilename,
		    cleaner::Parameters& parameters) -> void {

  // Check if we actually have to do anything
  auto alwaysGenerateFile = parameters.alwaysRegenerateFile();

  if (!alwaysGenerateFile) {
    alwaysGenerateFile = !util::exists(outFilename);    
    cout << "\n" << progname << ": " << outFilename
	 << " does not exist, so generating it" << endl;
  }

  // If we have to do something...
  if (alwaysGenerateFile) {

    auto start = chrono::steady_clock::now();
    cout << progname << ": " << infilename << " ->> " << outFilename << endl;

    auto sstream = stringstream{};
    sstream.precision(6);
    sstream << fixed;

    auto file = ifstream{infilename};
    auto line = string{};
    auto linesInFile = size_t{0};
    while (getline(file, line)) {
      linesInFile++;
    }

    file.close();
    cout << "There are " << linesInFile << " entries in the file" << endl;

    // Allocate enough space to store the file contents
    auto rows = Rows{linesInFile};

    auto inCount = 0ul;
    switch (parameters.getType()) {

    case SensorParameter::SensorType::PHONE_ACCELEROMETER:
    case SensorParameter::SensorType::PHONE_GYROSCOPE:
    case SensorParameter::SensorType::AX3_ACCELEROMETER:

      inCount = processKinematic(rows, infilename);
      break;
      
    case SensorParameter::SensorType::LOCATION:
    case SensorParameter::SensorType::GPS_LOC:

      inCount = processLocation(rows, infilename);
      break;
    
    default:
      cerr << "Didn't expect to get here" << endl;
      exit(EXIT_FAILURE);
    }
    
    cout << "\nRead the data in\n" <<  rows.size() << " rows read\n";
    cout << "----------------------------------------\n";

    if (parameters.detectSampleRate()) {
      auto sampleRateFilename = outFilename.stem();
      sampleRateFilename += filesystem::path("_rate");
      sampleRateFilename += ".txt";
      parameters.setSampleRate(getSampleRate(rows, sampleRateFilename));
    }
    
    // Remove the baseline. Only do this for the AX3 because it has a
    // constant data rate.  Need to think how to do it for the phone
    // data!
    if (parameters.getType() == SensorParameter::SensorType::AX3_ACCELEROMETER) {
      baseline(parameters,
	       rows,
	       Row::DataType::RAW,
	       Row::DataType::COOKED);
    }
  
    auto outCount = 0ul;

    switch (parameters.getType()) {
    case SensorParameter::SensorType::PHONE_ACCELEROMETER:
    case SensorParameter::SensorType::PHONE_GYROSCOPE:
    case SensorParameter::SensorType::AX3_ACCELEROMETER:
      outCount = Reduce().reduce(parameters, rows, outFilename);
      break;
      
    case SensorParameter::SensorType::LOCATION:
    case SensorParameter::SensorType::GPS_LOC:
      outCount = Reduce().noreduce(parameters, rows, outFilename);
      break;
    
    default:
      cerr << "Didn't expect to get here" << endl;
      exit(EXIT_FAILURE);
    }
  
    // Subsample kinematic data by taking the mean of all values in a
    // second and using that for the value for the second
  
    cout << inCount << " lines read, " << outCount << " lines written" << endl;
    auto seconds = chrono::duration_cast<chrono::seconds>(chrono::steady_clock::now() -
							  start).count();
    if (seconds) {
      cout << inCount / seconds << " lines per second\n\n";
      cout << seconds << " seconds elapsed" << endl;
    }
    util::allDone(cout, progname);
  }
  else {
    cout << progname << ": " << outFilename
	 << " already exists, so skipping it" << endl;
  }
}


/**
 * Configure STXXL.
 */
static auto config() -> void {
  // get uninitialized config singleton
  stxxl::config * cfg = stxxl::config::get_instance();
  
  // create a disk_config structure.
  auto disk1 = stxxl::disk_config{"/tmp/stxxl.tmp",
				  10000ul * 1024ul * 1024ul,
				  "syscall unlink"};
  disk1.direct = stxxl::disk_config::DIRECT_ON; // force O_DIRECT
  // add disk to config
  cfg->add_disk(disk1);
}


/**
 * Display command line usage
 */
static auto usage() {
  util::justify(cout, progname,
		"Clean AX3 and similar CSV data files");
  cout << progname << " [options] <infile> <outfile> [<type>]\n";
  cout << "\n";
  auto options = vector<Option>{};
  options.push_back(Option("-c","--cutoff", "Set cutoff frequency to specified value", true));
  options.push_back(Option("-f","--force","Causes output file to be skipped if already exists",
			   false, true));
  options.push_back(Option("-l","--force","Causes output file to be skipped if already exists"));
  options.push_back(Option("-s","--samplerate","Specifies sample rate in samples per second. "
			   "Default is to infer rate from data", true));
		 
  cout << "<type> is one of: gyroscope accelerometer ax3 location gpslocation\n";
  cout << "   Default is ax3\n";
  cout << "\n";
  Option::show(options);
  cout << "e.g. " << progname << " data.csv data-out.csv ax3\n";
}

/**
 * Entry point
 */
auto main(int argc, char** argv) -> int {
  // Need at least input file and output file
  if (argc < 2) {
    usage();
    return EXIT_FAILURE;
  }

  auto force = true;
  auto detectSampleRate = true;
  auto sampleRate = 0.;
  auto cutoff = 0.05;
  auto typeString = string{};
  auto inputFilename = string{};
  auto outputFilename = string{};
  auto nextIsSampleRate = false;
  auto nextIsCutOff = false;

  auto index = 1;
  while (index < argc) {
    if (argv[index][0] == '-') {
      if (argv[index][1] == '-') {
	
	auto option = util::locase(argv[index]);

	if (option == "--lazy") {
	  force = false;
	}
	else if (option == "--force") {
	  force = true;
	}
	else if (option == "--cutoff") {
	  nextIsCutOff = true;
	}
	else if (option == "--samplerate") {
	  detectSampleRate = false;
	  nextIsSampleRate = true;
	}
	else if (option == "--help") {
	  usage();
	  return EXIT_SUCCESS;
	}
	else {
	  cerr << "Unrecognised long option: " << argv[index] << endl;
	  usage();
	  return EXIT_FAILURE;
	}
      }
      else {
	for (auto&& opt : static_cast<string>(argv[index])) {
	  switch (opt) {
	  case '-':
	    break;
	  case 'c':
	    nextIsCutOff = true;
	    break;
	  case 'l':
	    force = false;
	    break;
	  case 'f':
	    force = true;
	    break;
	  case 's':
	    detectSampleRate = false;
	    nextIsSampleRate = true;
	    break;
	  default:
	    cerr << "Unrecognised option: " << argv[index] << endl;
	    usage();
	    return EXIT_FAILURE;
	  }
	}
      }
    }
    else if (nextIsSampleRate) {
      if (!util::strtonum(argv[index], sampleRate)) {	
	cerr << "Conversion error with sample rate, " << argv[index] << endl;
	return EXIT_FAILURE;
      }
      nextIsSampleRate = false;
    }
    else if (nextIsCutOff) {
      if (!util::strtonum(argv[index], cutoff)) {	
	cerr << "Conversion error with cutoff, " << argv[index] << endl;
	return EXIT_FAILURE;
      }
      nextIsCutOff = false;
    }
    
    else if (inputFilename.empty()) {
      inputFilename = argv[index];
    }
    else if (outputFilename.empty()) {
      outputFilename = argv[index];
    }
    else if (typeString.empty()) {
      typeString = argv[index];
    }
    else {
      cerr << "Extra parameter provided" << endl;
      return EXIT_FAILURE;
    } 
    index++;
  }
  

  
  // Handle defaults
  if (outputFilename.empty()) {
    auto filename = fs::path{inputFilename};
    filename.replace_filename(filename.stem().string() + "_clean"
			      + filename.extension().string());
    outputFilename = filename.string();
  }

  if (typeString.empty()) {
    typeString = cleaner::Parameters::DEFAULT_TYPE_STRING;
  }
  
  auto parameters = cleaner::Parameters{detectSampleRate,
					sampleRate,
					cutoff,
					typeString,
					force};
  parameters.show();
  cout << "----------------------------------------\n";
  cout << "Output format: " << Row::heading(parameters) << "\n";
  cout << "----------------------------------------" << endl; 

  config();

  auto file = ifstream{inputFilename};
  if (!filesystem::exists(inputFilename)) {
    cerr << "file " << inputFilename << " does not exist" << endl;
    return EXIT_FAILURE;
  }

  process(filesystem::path(inputFilename),
	  filesystem::path(outputFilename),
	  parameters);

    
  return EXIT_SUCCESS;
  
}
