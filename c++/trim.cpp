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
 * trim <filename> <threshold> <period>
 *
 * Jason Leake December 2019
 */

#include "Row.h"
#include "Rows.h"
#include "util.h"
#include <chrono>
#include <cmath>
#include <deque>
#include <execinfo.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <libfccp/csv.h>

using namespace std;
namespace fs = std::filesystem;

static constexpr auto DEBUG = false;
static constexpr auto programName = "trim";

/**
 * Main processing method.  Processes a single input file and produces
 * a single output file from it.
 *
 * @param infilename input filename
 * @param outfilename output filename
 * @param parameters run-time parameters setting
 */
auto process(const filesystem::path& inputFilename,
	     const filesystem::path& outputFilename,
	     int column,
	     double threshold,
	     double period,
	     bool generateFile) {

  if (generateFile) {
    cout << "\nforce flag set, so regenerating " << outputFilename << endl;
  }
  else if (!util::exists(outputFilename)) {
    generateFile = true;
    cout << "\n" << programName << " " << outputFilename
	 << " does not exist, so generating it" << endl;
  }

  // If we have to do something...
  if (generateFile) {
    auto inCount = 0ul;
    auto start = chrono::steady_clock::now();
    cout << programName << ": " << inputFilename << " ->> "
	 << outputFilename << endl;

    auto sstream = stringstream{};
    sstream.precision(6);
    sstream << fixed;
      auto seconds = chrono::duration_cast<chrono::seconds>(chrono::steady_clock::now() -
							  start).count();
    if (seconds) {
      cout << inCount / seconds << " lines per second\n\n";
      cout << seconds << " seconds elapsed" << endl;
    }
  }
  else {
    cout << programName << ": " << outputFilename
	 << " already exists, so skipping it" << endl;
  }
  util::allDone(cout, programName);
}

/**
 * Display command line usage
 */
auto usage() {
  util::justify(cerr, programName,
		"Removes accelerometer data where nothing is happening");
  cerr << programName << ": [options] <infile> <column> <threshold> <period> [<outfile>]\n";
  cerr << "\n";
  cerr << "Options:\n";
  cerr << "-l or --lazy causes output file to be regenerated only if does not exist" << endl;
}

/**
 * Entry point
 */
auto main(int argc, char** argv) -> int {
  // Need at least input file and output file
  if (argc < 3) {
    usage();
    return EXIT_FAILURE;
  }

  auto force = true;
  auto column = 0;
  auto columnDefined = false;
  auto threshold = 0.;
  auto period = 0.05;
  auto thresholdDefined = false;
  auto periodDefined = false;
  auto inputFilename = string{};
  auto outputFilename = string{};
  
  auto index = 1;
  while (index < argc) {
    if (argv[index][0] == '-') {
      auto option = string{argv[index]};
      
      if (option == "-l" || option == "--lazy") {
	force = false;
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
    else if (!columnDefined) {
      if (!util::strtonum(argv[index], column)) {
	cerr << "Conversion error with column number, " << argv[index] << endl;
	return EXIT_FAILURE;
      }
      columnDefined = true;
    }

    else if (!thresholdDefined) {
      if (!util::strtonum(argv[index], threshold)) {
	cerr << "Conversion error with threshold, " << argv[index] << endl;
	return EXIT_FAILURE;
      }
      thresholdDefined = true;
    }
    else if (!periodDefined) {
      if (!util::strtonum(argv[index], period)) {
	cerr << "Conversion error with period, " << argv[index] << endl;
	return EXIT_FAILURE;
      }
      periodDefined = true;
    }
    else if (outputFilename.empty()) {
      outputFilename = argv[index];
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
    filename.replace_filename(filename.stem().string() + "_trim"
			      + filename.extension().string());
    outputFilename = filename.string();
  }
  
  
  cout << "trim " << inputFilename  << " " << column <<
    " " << threshold << " " <<
    period << " " << outputFilename << endl;
  
  cout << "----------------------------------------\n";
  
  auto file = ifstream{inputFilename};
  if (!filesystem::exists(inputFilename)) {
    cerr << "file " << inputFilename << " does not exist" << endl;
    return EXIT_FAILURE;
  }
  
  process(filesystem::path(inputFilename),
	  filesystem::path(outputFilename),
	  column,
	  threshold,
	  period,
	  force);

  util::allDone(cout, programName);
  return EXIT_SUCCESS;
  
}
