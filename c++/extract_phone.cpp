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

// Convert data collected by the phone to similar data format used by
// AX3 CSV output.
//
// The AX3 format accelerometer data lines of the form:
// 2020-10-22 18:00:04.780,-1.043625,0.020250,-0.020250
// and we use this format for phone gyro and accelerometer data
//

/**
 * Jason Leake October 2019
 */

#include "PhoneDataConverter.h"
#include "util.h"
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <signal.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

using namespace std;

static constexpr auto programName = "extract_phone";

auto usage() {
  util::justify(cerr, programName,
		"This program extract particular field types from"
		" phone data files.");
  cerr << "Usage: " << programName << " [-s] <infile> <outfile> <type>" << endl;
  cerr << "-l, --lazy does not generate files if they already exist" << endl;
  cerr << "-s, --short stops processing after 100 lines have been output, for testing" << endl;
}

/**
 * Entry point
 */
auto main(int argc, char** argv) -> int {
  if (argc < 4) {
    usage();
    return EXIT_FAILURE;
  }


  auto typeString = string{};
  auto inputFilename = string{};
  auto outputFilename = string{};
  auto force = true;
  auto shortRun = false;
  
  auto index = 1;
  while (index < argc) {
    if (argv[index][0] == '-') {
      auto option = string{argv[index]};

      if (option == "-l" || option == "--lazy") {
	force = false;
      }
      else if (option == "-s" || option == "--short") {
	shortRun = true;
	cout << "Short run, terminating program when 100 lines written (-s present)" << endl;
      }      
      else {
	cerr << "Unrecognised option: " << argv[index] << endl;
	usage();
	return EXIT_FAILURE;
      }
    }
    else if (inputFilename.empty()) {
      inputFilename = argv[index];
    }
    else if (outputFilename.empty()) {
      outputFilename = argv[index];
    }
    else if (typeString.empty()) {
      typeString = argv[index];
      cout << typeString << endl;
    }
    else {
      cerr << "Extra parameter provided" << endl;
      return EXIT_FAILURE;
    }
 
    index++;
  }


  if (force || !util::exists(outputFilename)) {
  
    // Create output directories if they do not exist
    auto outpath = filesystem::path{outputFilename};
    if (!outpath.parent_path().empty() &&
	!filesystem::exists(outpath.parent_path())) {
      cout << "Creating output directory " << outpath.parent_path() << endl;
      filesystem::create_directories(outpath.parent_path());
    }
  
    auto outfile = ofstream{outputFilename};
    if (!outfile.is_open()) {
      cerr << "Unable to open output file " << outputFilename << endl;
      return EXIT_FAILURE;
    }
  
    // Check output directory exists
    if (!util::exists(inputFilename)) {
      return EXIT_FAILURE;
    }

    auto input = ifstream{inputFilename};
    auto line = string{};

    // Read the file and copy the records
    auto inCount = 0;
    auto outCount = 0;

    // Accelerations have the phone's m/s^2 converted to g to match the
    // way that we configure the AX3 configured.  Could put in an
    // auto-sense
    auto converter = PhoneDataConverter(typeString);

    while (getline(input, line)) {
    
      if (converter.match(line)) {
	auto newLine = converter.convert(line, inCount);
	if (newLine.size() > 0) {
	  outfile << newLine << "\n";
	  outCount++;
	}
      }
      if (inCount % 100000 == 0) {
	cout << inCount << " lines processed.\r";
	cout.flush();
      }
      inCount++;
      if (shortRun) {
	if (outCount >= 100) {
	  break;
	}
      }
    }
    cout << "\n" << inCount << " lines scanned, " << outCount << " written\n\n";
    input.close();
    outfile.close();
  }
  else {
    cout << outputFilename << " exists, so skipping it" << endl;
  }

  util::exitSuccess(programName);
}
