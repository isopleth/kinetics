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
 * Remove all entries outside of rectanguler bounding box
 *
 * Jason Leake October 2019
 */

#include "util.h"
#include "Row.h"
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <libfccp/csv.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <utility>
#include <getopt.h>

using namespace std;
namespace c = std::chrono;
namespace fs = std::filesystem;

// Contents of bounding box definition file
struct BoundingBox {
  double minLat;
  double maxLat;
  double minLon;
  double maxLon;
  BoundingBox(const string& filename);
  auto show() const {
    cout << "=====\n";
    cout << "minLat " << minLat << "\n";
    cout << "maxLat " << maxLat << "\n";
    cout << "minLon " << minLon << "\n";
    cout << "maxLon " << maxLat << "\n";
    cout << "=====\n";
  }
};

/**
 * Constructor
 *
 * @param filename name of file containing bounding box coordinates
 */
BoundingBox::BoundingBox(const string& filename) {
  auto file = ifstream{filename};
  auto str = string{};
  auto foundMask = 0;
  while (getline(file, str)) {
    auto fields = util::split(str,'=');
    
    if (fields.size() == 2) {
      if (fields[0] == "minLat") {
	minLat = stod(fields[1]);
	foundMask |= 0x1;
      }
      else if (fields[0] == "maxLat") {
	maxLat = stod(fields[1]);
	foundMask |= 0x2;
      }
      else if (fields[0] == "minLon")  {
	minLon = stod(fields[1]);
	foundMask |= 0x4;
      }
      else if (fields[0] == "maxLon") {
	maxLon = stod(fields[1]);
	foundMask |= 0x8;
      }
      else {
	cerr << "Unrecognised keyword " << fields[0] << endl;
      }
    }
    else {
      cerr << "Unrecognised line " << str << endl;
    }
  }
  if (foundMask != 15) {
    cerr << "Not all fields specified" << endl;
    exit(EXIT_FAILURE);
  }
  if (minLon > maxLon) {
    swap(minLon, maxLon);
  }
  if (minLat > maxLat) {
    swap(minLat, maxLat);
  }
}

const constexpr auto programName = "bounding_box";

/**
 * Main processing method.  Processes a single input file and produces
 * a single output file from it.
 *
 * @param infilename input filename
 * @param outfilename output filename
 * @param parameters run-time parameters setting
 */
auto process(const string& infilename,
	     const string& outfilename,
	     const BoundingBox& box) -> void {
  auto start = c::steady_clock::now();
  cout <<  infilename << " ->> " << outfilename << endl;

  auto in = io::CSVReader<7>{infilename};
  if (util::csvHasHeader(infilename, true)) {
    in.read_header(io::ignore_extra_column,
		   "datetime", "epoch", "latitude", "longitude",
		   "altitude", "accuracy","speed");
  }
  
  auto datetime = string{};
  auto epoch = 0ul;
  auto latitude = 0.0;
  auto longitude = 0.0;
  auto altitude = 0.0;
  auto accuracy = 0.0;
  auto speed = 0.0;
  auto inCount = 0ul;
  auto outCount = 0ul;
  auto outfile = ofstream{};
  static auto distance = 111045; // Metres per degree of lat and long
  const auto LOCATION = SensorParameter{SensorParameter::SensorType::LOCATION};
  
  while (in.read_row(datetime, epoch, latitude, longitude, altitude, accuracy, speed)) {
    inCount++;
    if (latitude <= box.maxLat && latitude >= box.minLat &&
	longitude <= box.maxLon && longitude >= box.minLon) {
      if (!outfile.is_open()) {
	cout << "  Open " << outfilename << endl;
	outfile = ofstream{outfilename};
	outfile.precision(17);
	outfile << Row::heading(LOCATION);
      }

      auto row = Row(datetime,
		     epoch,
		     (latitude - box.minLat) * distance,
		     (longitude - box.minLon) * distance,
		     altitude,
		     accuracy,
		     speed);
		     
      outfile << row.toString(LOCATION);
      outCount++;
    }
  }
  cout << inCount << " lines read, " << outCount << " lines written" << endl;
  auto seconds = c::duration_cast<c::seconds>(c::steady_clock::now() -
					      start).count();
  if (seconds) {
    cout << inCount / seconds << " lines per second\n\n";
    cout << seconds << " seconds elapsed" << endl;
  }
  util::allDone(cout, programName);
}


/**
 * Process file containing list of location records.  Writes to output file
 *
 * @param filename input file
 * @param box bounding box, coordinates outside of the box are thrown away
 * @param processData true to process data.  Otherwise just carry out the checks.
 */
auto processList(const string& filename,
		 const BoundingBox& box,
		 bool processData) -> void {
  cout << filename << endl;
  auto file = ifstream{filename};
  auto str = string{};
  auto skipRestOfFile = false;

  while (getline(file, str)) {
    cout << (skipRestOfFile ? "ignore: " : "") << str << endl;

    str = util::preprocessLine(str);
    if (str.empty()) {
      // Skip this line
      continue;
    }
        
    if (str == "exit") {
      cout << "Exit keyword, so ignoring the rest of the file\n";
      skipRestOfFile = true;
    }
    
    if (!skipRestOfFile) {  
      auto ssin = istringstream{str};
      auto infilename = string{};
      auto outfilename = string{};
      getline(ssin, infilename, '|');
      getline(ssin,  outfilename, '|');
      
      // Create output directories if they do not exist
      auto outpath = filesystem::path{outfilename};
      if (!outpath.parent_path().empty() &&
	  !filesystem::exists(outpath.parent_path())) {
	cout << "Creating output directory " << outpath.parent_path() << endl;
	filesystem::create_directories(outpath.parent_path());
      }
      
    }
  }
}

auto usage() -> void {
}

/**
 * Entry point
 */
auto main(int argc, char** argv) -> int {
  
  if (argc != 3) {
    cerr << "Usage: " << programName << " <input file> <location file>" << endl;
    return EXIT_FAILURE;
  }

  auto force = true;
  const auto shortOpts = "fh";
  const option longOpts[] = {{"lazy", no_argument, nullptr, 'l'},
			     {"force", no_argument, nullptr, 'f'},
			     {"help", no_argument, nullptr, 'h'},
			     {nullptr, no_argument, nullptr, 0}};

  while (true) {
    const auto opt = getopt_long(argc, argv, shortOpts, longOpts, nullptr);

    if (opt == -1) {
      break;
    }

    switch (opt) {
    case 'f':
      force = true;
      break;

    case 'h':
    case '?':
      usage();
      return EXIT_SUCCESS;
      
    case 'l':
      force = false;
      break;
    }    
  }

  auto inFilename = string{};
  auto outFilename = string{};
  auto locationFilename = string{};
  
  for (auto index = optind; index < argc; index++) {
    if (inFilename.empty()) {
      inFilename = argv[index];
    }
    else if (outFilename.empty()) {
      outFilename = argv[index];
    }
    else if (locationFilename.empty()) {
      locationFilename = argv[index];
    }
    else {
      cerr << "Too many command line arguments" << endl;
      usage();
      return EXIT_FAILURE;
    }
  }

  cout << programName << " " << inFilename << " ->> " << outFilename << endl;

  if (!util::exists(locationFilename)) {
    cerr << programName << ": " << locationFilename << " does not exist";
    return EXIT_FAILURE;
  }

  auto box = BoundingBox{locationFilename};
  box.show();

  if (force) {
    process(inFilename, outFilename, box);
  }
  else if (!fs::exists(outFilename)) {
  }
  return EXIT_SUCCESS;
}
