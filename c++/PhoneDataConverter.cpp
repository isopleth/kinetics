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
 * Convert line of phone data to match the format of the AX3 CSV data
 *
 * Jason Leake October 2019
 */

#include "PhoneDataConverter.h"
#include "util.h"
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <unistd.h>

using namespace std;
using Sensor = SensorParameter::SensorType;

/**
 * Constructor.
 *
 * @param searchString record prefix to search for.  This is the first
 * field of each record in the input CSV file.
 */
PhoneDataConverter::PhoneDataConverter(const string& searchString) {
  if (searchString == "ACCELEROMETER") {
    type = Sensor::PHONE_ACCELEROMETER;
  }
  else if (searchString == "GYROSCOPE") {
    type = Sensor::PHONE_GYROSCOPE;
  }
  else if (searchString == "GPS_LOC") {
    type = Sensor::GPS_LOC;
  }
  else if (searchString == "LOCATION") {
    type = Sensor::LOCATION;
  }
  else {
    cerr << "Unsupported search string" << endl;
    exit(EXIT_FAILURE);
  }
  cout << "Type is " << static_cast<int>(type)
       << " (" << getTypeString() << ")" << endl;
}

/**
 * Convert date time from phone format to AX3 CSV format
 *
 * @param datetime date time string read from phone file
 * @return datetime in AX3 CSV format
 */
auto PhoneDataConverter::convertDatetime(const string& datetime) -> string {
  // e.g. 24-Feb-2020 23:00:00.0070 +0100
  struct tm tm = {};
  
  // 2020-11-23 14:00:04
  auto stringstream = istringstream{datetime};
  stringstream >> get_time(&tm, "%d-%b-%Y %H:%M:%S");
  
  auto timezone = stoi(datetime.substr(26));
  switch (timezone) {
    
  case 0:
    tm.tm_isdst = 0;
    break;

  case 100:
    tm.tm_isdst = 1;
    break;
    
  default:
    break;
  }
  
  auto sso = ostringstream{};
  sso << put_time(&tm, "%Y-%m-%d %H:%M:%S") << ".";

  auto subsecond = static_cast<float>(stoi(datetime.substr(21,4),0,10));
  // Convert milliseconds to hundredths of a second and round
  auto subsecondInt = static_cast<int>(round(subsecond / 10));

  auto subsecondStr = to_string(subsecondInt);

  auto len = subsecondStr.length();
  if (len < 3) {
    auto leadingZeros = 3 - subsecondStr.length();
    for (auto count = size_t{0}; count < leadingZeros; count++) {
      sso << "0";
    }
  }
  sso << subsecondStr;
  return sso.str();
}

/**
 * Process location data record
 *
 * @param fields fields of record
 * @param line raw record, for error messages
 * @param lineNumber sequential record number, for error messages
 * @return corresponding record to be written to output file.
 */
auto PhoneDataConverter::processGenericLocation(const vector<string>& fields,
						const string& line,
						size_t lineNumber) -> string {


  if (fields.size() != 9) {
    cout << "Line " << lineNumber << ": Incomplete loc record: "
	 << line << endl;
    return util::errorReturnString(__FILE__,__LINE__);
  }
  
  auto latitude = fields[4];
  if (!util::isNumber(latitude)) {
    return util::errorReturnString(__FILE__,__LINE__);
  }
  auto longitude = fields[5];
  if (!util::isNumber(longitude)) {
    return util::errorReturnString(__FILE__,__LINE__);
  }
  
  auto altitude = fields[6];
  if (!util::isNumber(altitude)) {
    return util::errorReturnString(__FILE__,__LINE__);
  }

  auto accuracy = fields[7];
  if (!util::isNumber(accuracy)) {
    return util::errorReturnString(__FILE__,__LINE__);
  }
  
  auto speed = fields[8];
  if (!util::isNumber(speed)) {
    return util::errorReturnString(__FILE__,__LINE__);
  }

  // Need to change the format of the date records as they have
  // trailing time offset

  return convertDatetime(fields[1]) + "," +
    latitude + "," + longitude + "," + altitude + "," + accuracy + "," + speed;
}

// One of FUSED_LOC, GPS_LOC and NETWORK_LOC
auto PhoneDataConverter::processSpecificLocation(const vector<string>& fields,
						 const string& line,
						 size_t lineNumber) -> string {
  
  if (fields.size() != 9) {
    cout << "Line " << lineNumber << ": Incomplete gen loc record: "
	 << line << endl;
    return util::errorReturnString(__FILE__,__LINE__);
  }
  
  auto latitude = fields[4];
  if (!util::isNumber(latitude)) {
    return util::errorReturnString(__FILE__,__LINE__);
  }
  auto longitude = fields[5];
  if (!util::isNumber(longitude)) {
    return util::errorReturnString(__FILE__,__LINE__);
  }
  
  auto altitude = fields[6];
  if (!util::isNumber(altitude)) {
    return util::errorReturnString(__FILE__,__LINE__);
  }

  auto accuracy = fields[7];
  if (!util::isNumber(accuracy)) {
    return util::errorReturnString(__FILE__,__LINE__);
  }
  
  auto speed = fields[8];
  if (!util::isNumber(speed)) {
    return util::errorReturnString(__FILE__,__LINE__);
  }

  // Need to change the format of the date records as they have
  // trailing time offset

  return convertDatetime(fields[1]) + "," +
    latitude + "," + longitude + "," + altitude
    + "," + accuracy + "," + speed;
}

/**
 * Process kinematic data record
 *
 * @param fields fields of record
 * @param line raw record, for error messages
 * @param lineNumber sequential record number, for error messages
 * @return corresponding record to be written to output file.
 */
auto PhoneDataConverter::processKinematic(const vector<string>& fields,
					  const string& line,
					  size_t lineNumber) -> string {
  
  if (fields.size() < 6) {
    cout << "Line " << lineNumber << ": Incomplete record: " << line << endl;
    return util::errorReturnString(__FILE__,__LINE__);
  }
  
  auto x = fields[3];
  if (!util::isNumber(x)) {
    return util::errorReturnString(__FILE__,__LINE__);
  }
  
  auto y = fields[4];
  if (!util::isNumber(y)) {
    return util::errorReturnString(__FILE__,__LINE__);
  }
  
  auto z = fields[5];
  if (!util::isNumber(z)) {
    return util::errorReturnString(__FILE__,__LINE__);
  }

  // Convert accelerations from m/s^2 to g
  if (type == Sensor::PHONE_ACCELEROMETER) {
    x = toStandardGravity(x);
    y = toStandardGravity(y);
    z = toStandardGravity(z);
  }
  // Need to change the format of the date records as they have
  // trailing time offset

  return convertDatetime(fields[1]) + "," + x + "," + y + "," + z;
}

/**
 * Convert one line of the file from "phone" format to AX3 CSV
 * format.
 */
auto PhoneDataConverter::convert(const string& line,
				 size_t lineNumber) -> string {
  auto fields = util::split(line, ',');

  switch (type) {
  case Sensor::PHONE_ACCELEROMETER:
  case Sensor::PHONE_GYROSCOPE:
    return processKinematic(fields, line, lineNumber);

  case Sensor::GPS_LOC:
    return processSpecificLocation(fields, line, lineNumber);
    break;

  case Sensor::LOCATION:
    return processGenericLocation(fields, line, lineNumber);
    break;

  default:
    return "";
  }
}

/**
 * Convert values in metres/second squared to g
 *
 * @param value string representation of value to convert
 * @return string representation of converted value
 */
auto PhoneDataConverter::toStandardGravity(const string& value) -> string {
  // Standard gravity
  static constexpr auto STANDARD_GRAVITY = double{9.80665};

  auto val = stod(value);
  val = val / STANDARD_GRAVITY;
  auto ss = stringstream{};
  ss << val;
  return ss.str();
}

/**
 * Count the number of lines in the file.
 *
 * @param filename file to count lines in
 * @return number of lines
 */
auto PhoneDataConverter::countLines(const string& filename) -> int {
  cout << "Counting lines in file" << endl;
  auto input = ifstream(filename);
  auto line = string{};
  
  // Read the file and copy the accelerometer records
  auto index = 0;
  while (getline(input, line)) {
    index++;
  }
  return index;
}

/**
 * Determine if the line corresponds to the particular type that the
 * phone converter object is looking for.  The constructor is called
 * with a search string, which is mapped onto a particular data type.
 * When this method is called, it returns true if the line passed in
 * the method call corresponds to that type, or false if it does not.
 * i.e. it is used to filter out all records which do not correspond
 * to the desired type.
 *
 * @param line line read from data file to check
 * @return true if this is to be processed
 */
auto PhoneDataConverter::match(const string& line) const -> bool{
  auto searchStringComma = string{};
  
  switch (type) {
  case Sensor::PHONE_ACCELEROMETER:
    return line.rfind("ACCELEROMETER,") == 0;

  case Sensor::PHONE_GYROSCOPE:
    return line.rfind("GYROSCOPE,") == 0;
    
  case Sensor::GPS_LOC:
    return line.rfind("GPS_LOC,") == 0;
    
  case Sensor::LOCATION:
    // Look for any location record
    return (line.rfind("GPS_LOC,") == 0) ||
      (line.rfind("FUSED_LOC,") == 0) ||
      (line.rfind("NETWORK_LOC,") == 0);
    
  default:
    cerr << "Unsupported type in PhoneDataConverter::match()" << endl;
    exit(EXIT_FAILURE);
    break;

  }
  return false;
}

/**
 * Getter for type
 *
 * @return sensor type
 */
auto PhoneDataConverter::getType() const -> Sensor {
  return type;
}

/**
 * Getter for type description string
 *
 * @return type description string
 */
auto PhoneDataConverter::getTypeString() const -> string {
  switch (type){
  case Sensor::PHONE_ACCELEROMETER:
    return "ACCELEROMETER";
    
  case Sensor::PHONE_GYROSCOPE:
    return "GYROSCOPE";
    
  case Sensor::GPS_LOC:
    return "GPS_LOC";
    
  case Sensor::LOCATION:
    return "GPS_LOC or NETWORK_LOC or FUSED_LOC";
    
  default:
    return "unrecognised/unsupported";
  }
}


