/**
 * Split location file into several files separated by intervals when
 * no data was collected.
 *
 * Jason Leake October 2019
 */

#include "util.h"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <libfccp/csv.h>
#include <list>
#include "Row.h"

using namespace std;

static constexpr auto progname = "split_times";

/**
 * Construct the next output filename
 * @param parent parent directory
 * @param infilePath input filename from which output name is constructed
 * @param index index of output file
 * @return output filename
 */
auto makeOutfilename(const filesystem::path& parent,
		     const filesystem::path& infilePath,
		     int index) {
  auto outfilestub = infilePath.filename();
  auto outfileStem = infilePath.stem();
  auto outfileExtension = infilePath.extension();
  auto outfilePath = outfileStem;
  outfilePath += filesystem::path("_" + to_string(index));
  outfilePath += outfileExtension;
  return parent / outfilePath;
}

auto process(const filesystem::path& inputFilename,
	     const unsigned long& seconds,
	     bool force) {
  
  cout << "Splitting " << inputFilename << " (seconds is " <<
    seconds << ")" << endl;

  // Check if input file exists
  if (!util::exists(inputFilename)) {
    return;
  }

  auto in = io::CSVReader<7>{inputFilename};
  auto lastEpoch = 0ul;
  auto lastDatetime = string{};
  in.read_header(io::ignore_extra_column,
		 "datetime", "epoch", "latitude", "longitude",
		 "altitude",
		 "accuracy","speed");
  auto datetime = string{};
  auto epoch = 0ul;
  auto latitude = 0.;
  auto longitude = 0.;
  auto altitude = 0.;
  auto accuracy = 0.;
  auto speed = 0.;
  auto index = 1;

  auto outpath = inputFilename.parent_path();
  filesystem::create_directories(outpath);

  auto outfilefull = makeOutfilename(outpath, inputFilename, index++);
  auto generate = force;
  if (!generate && !filesystem::exists(outfilefull)) {
    cout << outfilefull << " does not exist, so generating it" << endl;
    generate = true;
  }

  if (generate) {
    cout << "  Opening " << outfilefull << endl;
    auto outfile = ofstream{outfilefull};

    const auto LOCATION = SensorParameter{SensorParameter::SensorType::LOCATION};
    while (in.read_row(datetime, epoch, latitude,
		       longitude, altitude, accuracy, speed)) {
      if (epoch - lastEpoch > seconds) {
	if (lastEpoch != 0) {
	  cout << "  -->> Step in times - "
	       << lastDatetime << " " << datetime << endl;
	  // Close current output file and open a new one
	  outfile.close();
	}
      }
      lastDatetime = datetime;
      lastEpoch = epoch;
      if (!outfile.is_open()) {
	outfilefull = makeOutfilename(outpath, inputFilename, index++);
	cout << "  Opening " << outfilefull << endl;
	outfile = ofstream{outfilefull};
      }

      auto row = Row(datetime,
		     latitude,
		     longitude,
		     altitude,
		     accuracy,
		     speed);
		     
      outfile << row.toString(LOCATION, false);
    }
    cout << endl;
  }
  else {
    cout << outfilefull << " already exists, skipping" << endl;
  }
}

void usage() {
  cout << "Usage: " << progname << " <seconds> [-l] <input files>" << endl;
}

/**
 * Entry point
 */
auto main(int argc, char** argv) -> int {

  if (argc < 3) {
    usage();

    return EXIT_FAILURE;
  }

  auto seconds = 0u;
  auto haveSeconds = false;
  auto inputFilenames = list<filesystem::path>{};
  

  auto force = true;
  for (auto index = 1; index < argc; index++) {
    if (argv[index][0] == '-') {
      if (static_cast<string>(argv[index]) == "-l") {
	force = false;
      }
      else if (static_cast<string>(argv[index]) == "--lazy") {
	force = false;
      }
      else {
	cerr << "Unrecognised option " << argv[index] << endl;
	usage();
      }
    }
    else if (!haveSeconds) {
      try {
	seconds = static_cast<unsigned>(stoul(argv[index]));
	haveSeconds = true;
      } catch (const invalid_argument& e) {
	cerr << "Invalid numeric argument: " <<argv[index] << endl;
	return EXIT_FAILURE;
      } catch (const out_of_range& e) {
	cerr << "Out of range: " <<argv[index] << endl;
	return EXIT_FAILURE;
      }
    }
    else {
      inputFilenames.push_back(static_cast<filesystem::path>(argv[index]));
      cout << " " << argv[index];
    }
    cout << endl;
  }
  
  for (auto&& inputFilename : inputFilenames) {
    process(inputFilename, seconds, force);
  }

  util::allDone(cout, progname);
  return EXIT_SUCCESS;
}
