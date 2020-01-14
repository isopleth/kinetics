/**
 * Encapsulates row read from data file.
 *
 * Jason Leake October 2019
 */

#include "Row.h"
#include <array>
#include <iostream>
#include <cmath>
#include <sstream>
#include <iomanip>
#include <cassert>
#include "SquareMatrix.h"
#include "util.h"

using namespace std;
using Sensor = SensorParameter::SensorType;


/**
 * Default constructor.
 */
Row::Row() {
  datetime = "";
  for (auto index = size_t{0}; index < Rowcons::COLUMNS; index++) {
    at(index) = 0;
  }
}

/**
 * Constructor
 *
 * @param datetime date time
 * @param x1 x
 * @param y1 y
 * @param z1 z
 */
Row::Row(const string& datetime,
	 const double x,
	 const double y,
	 const double z) :
  datetime{datetime} {
  at(0) = x;
  at(1) = y;
  at(2) = z;
  for (auto index = size_t{3}; index < Rowcons::COLUMNS; index++) {
    at(index) = 0;
  }
}

/**
 * Constructor
 *
 * @param datetime date time
 * @param x1 x
 * @param y1 y
 * @param z1 z
 * @param x2 xx
 * @param y2 yy
 * @param z2 zz
 */
Row::Row(const string& datetime,
	 const double x1,
	 const double y1,
	 const double z1,
	 const double x2,
	 const double y2,
	 const double z2) :
  datetime{datetime} {
  at(0) = x1;
  at(1) = y1;
  at(2) = z1;
  at(3) = x2;
  at(4) = y2;
  at(5) = z2;
}

/**
 * Truncate data by setting LSBs of the raw accelerometer
 * reading to zero. This removes random noise, or very
 * slight movements caused by things like passing traffic
 *
 * @param value value to mask
 * @param bitmask the bitmask to use
 * @return input value with mask applied
 */
auto Row::truncate(int val, unsigned bitmask) -> int {
  // Twos complement values are tricky for clearing the LSB, so make
  // them positive, then clear the bit and then set them back to
  // negative again.
  auto negative = val < 0;
  if (negative) {
    val = -val;
  }
    
  // XOR away bitmask that needs clearing
  // val at this point is definitely positive
  val = (val | bitmask) ^ bitmask;
  if (negative) {
    val = -val;
  }
    
  // Convert back to units of g
  return val;
}
  
/**
 * Round data by setting the LSB of the raw accelerometer reading to
 * zero.  The OpenMovement AX3 accelerometer, or more likely the
 * software to read it, outputs the data in units of g, but the
 * accelerometer clearly reads it in units of QUANTUM.
 */
auto Row::quantize(double value) -> int {
  // Internally the accelerometer seems to operate in
  // units of QUANTUM.  Convert to the actual amount of
  // units.
  auto quanta = round(value / QUANTUM);
  
  if (isnan(quanta)) {
    cerr << "Not a number" << quanta <<  endl;
    cerr.flush();
    exit(EXIT_FAILURE);
  }
  
  // Make sure we have the quantum correct
  if (fabs(quanta * QUANTUM - value) > fabs(quanta/10.)) {
    cerr << "Have you got the quantum correct? " <<
      (quanta * QUANTUM) << " versus " << value << endl;
    cerr.flush();
    exit(EXIT_FAILURE);
  }
  
  auto intVal = static_cast<int>(quanta);
  return intVal;
}

/**
 * Convert datetime to seconds since 1/1/70
 *
 * @param millisecondsEpoch true for epoch in milliseconds, false for seconds
 * @return epoch date time
 */
auto Row::getDatetimeEpoch(bool millisecondsEpoch) const -> unsigned long {
  struct tm tm = {};
  
  // e.g. 2019-07-22 15:00:04
  auto ss = istringstream(datetime.substr(0,19));
  ss >> get_time(&tm, "%Y-%m-%d %H:%M:%S");
  auto epoch =  mktime(&tm);
  if (millisecondsEpoch) {
    return epoch * 1000 + getDateTimeMillis();
  }
  else if (getDateTimeMillis() >= 500) {
    epoch++;
  }
  return epoch;
}



/**
 * Get the milliseconds component of the date time, if there is one
 *
 * @return milliseconds, or 0 if none
 */
auto Row::getDateTimeMillis() const -> unsigned long {
  if (datetime.size() > 19) {
    auto millisString = datetime.substr(20,3);
    if (util::isNumber(millisString)) {
      auto millis = stoul(millisString);
      auto power = millisString.length() - 3;
      while (power < 3) {
	millis = millis * 10;
	power++;
      }
      return millis;
    }    
  }
  return 0;
}


/**
 * Convert data of the specified datatype to a set of string values
 * separated by a comma.
 */
auto Row::sstringValues(stringstream& sstream,
			const SensorParameter& parameters, 
			DataType dataType) const -> void {
  sstream.precision(12);
  auto acc = 0.0;
  for (auto axis = size_t{0}; axis < 3; axis++) {
    sstream << ",";
    auto val = at(3*static_cast<size_t>(dataType) + axis);
    sstream << val;
    // Need sum of squares for total acceleration
    if (parameters.isAcceleration()) {
      acc += val*val;
    }
  }
  if (parameters.isGyro()) {
    // Total rotation
    sstream << ",";
    sstream << totalRotation(at(3*static_cast<size_t>(dataType)),
			     at(3*static_cast<size_t>(dataType) + 1),
			     at(3*static_cast<size_t>(dataType) + 2));
  }
  else if (parameters.isAcceleration()) {
    // Total acceleration
    sstream << ",";
    sstream << sqrt(acc);
  }
  else {
    // No special value output
  }
}

/**
 * Output comma separated values to specified sstream
 */
auto Row::sstringValues(stringstream& sstream,
			unsigned long count,
			const SensorParameter& parameters) const -> void {
  sstream.precision(6);
  for (auto index = size_t{0}; index < count; index++) {
    sstream << ",";
    sstream << at(index);
  }
}

/**
 * Compute total rotation from three axes rotation
 * @param x rotation about x axis
 * @param y rotation about y axis
 * @param z rotation about z axis
 */
auto Row::totalRotation(double x, double y, double z) -> double {
  
  auto X = SquareMatrix{};
  auto Y = SquareMatrix{};
  auto Z = SquareMatrix{};
  
  X.setIdentity();
  X.set(1, 1, cos(x));
  X.set(1, 2, -sin(x));
  X.set(2, 1, sin(x));
  X.set(2, 2, cos(x));
  
  Y.setIdentity();
  Y.set(0, 0, cos(y));
  Y.set(0, 2, sin(y));
  Y.set(2, 0, -sin(y));
  Y.set(2, 2, cos(y));
    
  Z.setIdentity();
  Z.set(0, 0, cos(z));
  Z.set(0, 1, -sin(z));
  Z.set(1, 0, sin(z));
  Z.set(1, 1, cos(z));
    
  auto R = Z * Y * X;
  auto totalRotation = toDegrees(acos((R.trace() - 1.0) / 2.0));
  return totalRotation;
}


/**
 * Get date time field
 *
 * @return date time string
 */
auto Row::getDatetime() const -> string {
  return datetime;
}

/**
 * Replace a value in the row
 */
auto Row::putValue(DataType dataType,
		   size_t axis, double value) -> void {
  auto column = 3*static_cast<size_t>(dataType) + axis;
  at(column) = value;
}

/**
 * Return the column headings for the CSV output file
 *
 * @param type sensor data type
 * @return column headings for this sensor data type
 */
auto Row::heading(const SensorParameter& parameters) -> string {
  switch (parameters.getType()) {
  case Sensor::PHONE_GYROSCOPE:
  case Sensor::PHONE_ACCELEROMETER:
    return KINETIC_HEADER;

  case Sensor::AX3_ACCELEROMETER:
    return KINETIC_PLUS_HEADER;

  case Sensor::GPS_LOC:
  case Sensor::LOCATION:
    return LOCATION_HEADER;
  default:
    cerr << "Unsupported type\n";
    exit(EXIT_FAILURE);
  }
}

/**
 * Convert to text
 *
 * @param type sensor type
 * @return string representation
 */
auto Row::toString(const SensorParameter& parameters,
		   bool millisecondsEpoch) const -> string {
  auto sstream = stringstream{};

  sstream << datetime;
  sstream << ",";
  sstream << getDatetimeEpoch(millisecondsEpoch);

  if (parameters.isLocation()) {
    // RAW and COOKED don't really have any meaning here.  We just use
    // the data as a set of data fields.
    sstringValues(sstream, 5, parameters);
   
  }
  else {
    sstringValues(sstream, parameters, DataType::RAW);
    // We don't do baseline removal for phone data at the moment because
    // it has variable data rate
    if (parameters.getType() == Sensor::AX3_ACCELEROMETER) {
      sstringValues(sstream, parameters, DataType::COOKED);
    }
  }

  // The AX3 CSV files have MSDOS file endings    
  sstream << "\r" << endl;
  return sstream.str();
}

/**
 * Convert radians to degrees
 * 
 * @param radians radians to convert
 * @return degrees corresponding to radians value
 */
auto Row::toDegrees(double radians) -> double {
  return radians * 180. / M_PI;
}
