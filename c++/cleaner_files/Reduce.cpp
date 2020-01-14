/**
 * Reduce dataset size by subsampling.
 *
 * Jason Leake October 2019
 */

#include "Mean.h"
#include "Row.h"
#include "Rows.h"
#include "cleaner_files/Reduce.h"
#include "util.h"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>

using namespace std;
using namespace cleaner;

/**
 * Subsample by aggregating all the values read in each second into a
 * mean value for that second.  It writes the reduced file to the
 * output stream.
 *
 * @param parameters run-time parameters.  The only one we care
 * about is the data type - ax3 or phone accelerometer, or phone gyro
 * @param rows data rows
 * @param out output file to write results to
 * @return number of lines of output written
 */
auto Reduce::reduce(const Parameters& parameters,
		    Rows& rows,
		    const filesystem::path& outFilePath) -> unsigned long {
  util::makeDirectories(outFilePath);
  auto out = ofstream{outFilePath};
  if (!out) {
    cerr << "Unable to open " << outFilePath << endl;
    return 0;
  }
  auto rowCount = 0ul;
  auto outCount = 0ul;
  // Sub-sampling.  Replace all the values in a particular second with
  // the mean of them all
  auto oldSecond = 0ul;
  auto first = true;
  auto datetime = string{};
  auto means = array<Mean, 6>{};

  out << Row::heading(parameters);
  for (auto rowIndex = size_t{0}; rowIndex < rows.size(); rowIndex++) {
    // Subsampling
    rowCount++;

    auto lsecond = rows.getSecond(rowIndex);
    // Check if we have moved on to a new second
    if (lsecond != oldSecond) {
      oldSecond = lsecond;
      if (first) {
	// First value processed in run.  Nothing to see here.
	first = false;
      } else {
	// Second has rolled over. So, output the values.
	// There actually seem to be slightly more than 100 values at "100
	// samples per second" - more like 104.  Probably some clock
	// quantisation problem in the OpenMovement AX3 unit
	// Get rid of fractional part of datetime
	auto theRow = Row{datetime.substr(0,19),
			  means[0].getAverage(),
			  means[1].getAverage(),
			  means[2].getAverage(),
			  means[3].getAverage(),
			  means[4].getAverage(),
			  means[5].getAverage()};
	out << theRow.toString(parameters, false);
	outCount++;

	// Clear down the means
	for(auto&& s: means) {
	  s.reset();
	}

	if (rowCount % 1'000'000 == 0) {
	  cout << rowCount << " lines processed\r";
	  cout.flush();
	}

	outCount++;
      }
    }
    datetime = rows.getDatetime(rowIndex);

    auto index = 0ul;
    for(auto&& s: means) {
      s.add(rows.getValue(rowIndex, index++));
    }
  }
  out.close();

  return outCount;
}


/**
 * Null subsampling.  Just copy the input file to the output file, but
 * add epoch.
 *
 * @param parameters run-time parameters.  The only one we care
 * about is the data type - ax3 or phone accelerometer, or phone gyro
 * @param rows data rows
 * @param out output file to write results to
 * @return number of lines of output written
 */
auto Reduce::noreduce(const Parameters& parameters,
		      Rows& rows,
		      const filesystem::path& outFilePath) -> unsigned long {
  util::makeDirectories(outFilePath);
  auto out = ofstream{outFilePath};
  if (!out) {
    cerr << "Unable to open " << outFilePath << endl;
    return 0;
  }

  auto outCount = 0ul;
  // Sub-sampling.  Replace all the values in a particular second with
  // the mean of them all
  auto datetime = string{};
  out << Row::heading(parameters);
  for (auto rowIndex = size_t{0}; rowIndex < rows.size(); rowIndex++) {
    auto theRow = Row{rows.getDatetime(rowIndex),
		      rows.getValue(rowIndex, 0),
		      rows.getValue(rowIndex, 1),
		      rows.getValue(rowIndex, 2),
		      rows.getValue(rowIndex, 3),
		      rows.getValue(rowIndex, 4),
		      rows.getValue(rowIndex, 5)};
    out << theRow.toString(parameters, false);
    outCount++;
  }
  out.close();

  return outCount;
}
