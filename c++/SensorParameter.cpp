/**
 * Sensor parameter
 *
 * Jason Leake January 2020
 */

#include <iostream>
#include <stdexcept>
#include "SensorParameter.h"

using namespace std;

/**
 * Constructor
 *
 * @param typeString data type
 */
SensorParameter::SensorParameter(const string& typeString) {
  generateMapping();

  auto it = mapping.find(typeString);
  if (it != mapping.end()) {
    type = it->second;
  }
  else {
    cerr << "Supported sensor types are " << knownSensors() << "\n";
    cerr << "Specified sensor type is " << typeString << endl;
    throw runtime_error("Specified type is not supported.");
  }
}

/**
 * Constructor
 *
 * @param type data type
 */
SensorParameter::SensorParameter(SensorParameter::SensorType type) : type(type) {
  generateMapping();
}

auto SensorParameter::generateMapping() -> void { 
  // Lazy generation of mapping between typeString and data types enum
  if (mapping.size() == 0) {
    mapping["ax3"] = SensorParameter::SensorType::AX3_ACCELEROMETER;
    mapping["gyroscope"] = SensorParameter::SensorType::PHONE_GYROSCOPE;
    mapping["accelerometer"] = SensorParameter::SensorType::PHONE_ACCELEROMETER;
    mapping["location"] = SensorParameter::SensorType::LOCATION;
    mapping["gpslocation"] = SensorParameter::SensorType::GPS_LOC;
  }
}

/**
 * Return string containing list of supported data types
 *
 * @return string containing comma separated list of types
 */
auto SensorParameter::knownSensors() -> string {
  auto retval = string{};
  for (auto const& element : mapping) {
    if (retval.size()){
      retval += ", ";
    }
    retval += element.first;
  }
  return retval;
}


/**
 * Return true if the input file is gyro data
 */
auto SensorParameter::isGyro() const -> bool {
  return type == SensorType::PHONE_GYROSCOPE;}

/**
 * Return true if the input file is location data.
 */
auto SensorParameter::isLocation() const -> bool {
  return !(isGyro() || isAcceleration());
}

/**
 * Return true if the input file is acceleration data.
 */
auto SensorParameter::isAcceleration() const -> bool {
  return type == SensorType::AX3_ACCELEROMETER ||
    type == SensorType::PHONE_ACCELEROMETER;
}


map<string, SensorParameter::SensorType> SensorParameter::mapping;
