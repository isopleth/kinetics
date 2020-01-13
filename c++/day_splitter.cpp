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
 * Split file into one new file per day
 *
 * It relies upon the first entry in each line being an date field of the form
 * 2020-11-31 12:44:22.0284,
 *
 * Jason Leake October 2019
 */

#include "util.h"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <libfccp/csv.h>
#include <list>

using namespace std;

/**
 * Entry point
 */
auto process(const filesystem::path& infilename, bool lazy) {

  if (!util::exists(infilename)) {
    return EXIT_FAILURE;
  }

  // Create output directories if they do not exist
  auto outpath = filesystem::path(infilename).parent_path();

  auto outfilestub = filesystem::path(infilename).filename();

  auto datetime = string{};
  auto line = string{};

  auto olddate = string{};
  auto infile = ifstream{infilename};
  auto outfile = ofstream{};

  auto skipLine = false;
  auto hasHeader = util::csvHasHeader(infilename);
  auto header = string{};
  auto firstLine = true;
  auto generateOutputFile = true;
	
  while (getline(infile, line)) {    
    if (firstLine) {
      if (hasHeader) {
	header = line;
	skipLine = true;
      }
      firstLine = false;
    }
    
    if (!skipLine) {
      auto date = line.substr(0,10);
      if (date != olddate) {
	if (outfile.is_open()) {
	  outfile.close();
	}
	auto outfilename = outpath /
	  filesystem::path(date + "_" + outfilestub.string());
	
	if (lazy) {
	  generateOutputFile = !util::exists(outfilename);
	}
	
	if (generateOutputFile) {
	  cout << "  Creating " << outfilename << endl;
	  outfile = ofstream{outfilename};
	  if (hasHeader) {
	    outfile << header << "\r\n";
	  }
	}
	else {
	  cout << "Skip already existing " << outfilename << endl;
	}
	olddate = date;

      }
      if (generateOutputFile) {
	outfile << line;
	outfile << "\r\n";
      }
    }
    skipLine = false;
  }
  
  return EXIT_SUCCESS;
}

/**
 * Entry point
 */
auto main(int argc, char** argv) -> int {

  constexpr auto programName = "day_splitter";
  if (argc < 2) {
    util::justify(cerr, programName,
		  "This program splits accelerometer CSV files up "
		  "into individual per-day files.  This both reduces the "
		  "size of the individual files and makes it easier to "
		  "visualise the contents.");
    cerr << "Usage: " << programName << " [-l] <input_file ...>\n";
    cerr << "\n";
    cerr << "-l, or --lazy means don't regenerate the file if it already exists" << endl;
    return EXIT_FAILURE;
  }

  auto lazy = false;

  cout << programName;

  auto filenames = list<filesystem::path>{};
  for (auto index = 1; index < argc; index++) {

    if (static_cast<string>(argv[index]) == "-l") {
      lazy = true;
    }
    else if (static_cast<string>(argv[index]) == "--lazy") {
      lazy = true;
    }
    else {
      filenames.push_back(static_cast<filesystem::path>(argv[index]));
      cout << " " << argv[index];
    }
  }

  cout << endl;
  for (auto&& filename : filenames) {
    process(filename, lazy);
  }

  util::allDone(cout, programName);

  return EXIT_SUCCESS;
}
