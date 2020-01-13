/**
 * Parameters controlling program operation.
 *
 * Jason Leake October 2019
 */

#include "cleaner_files/Parameters.h"
#include <iostream>
#include <stdexcept>

using namespace std;
using namespace cleaner;

/**
 * Constructor
 *
 * @param detectSampleRate true to automatically detect sample rate
 * @param sampleRate data sample rate in Hz (ignored if detectSampleRate is true)
 * @param cutoff high pass filter cutoff frequency in Hz
 * @param typeString data type
 * @param forceFileRegeneration regenerate output file if exists, else skip
 */
Parameters::Parameters(bool detectSampleRate,
		       double sampleRate,
		       double cutoff,
		       const string& typeString,
		       bool forceFileRegeneration):
  SensorParameter(typeString),
  detectRate(detectSampleRate),
  sampleRateSet(!detectSampleRate),
  sampleRate(sampleRate),
  cutoff(cutoff),
  forceFileRegeneration(forceFileRegeneration) {

}


auto Parameters::show() const -> void {
 
  cout << "----------------------------------------\n";
  switch (getType()) {
  case Parameters::SensorType::PHONE_GYROSCOPE:
    cout << "Data is phone gyro data.  No baselining will be done\n";
    break;
  case Parameters::SensorType::PHONE_ACCELEROMETER:
    cout << "Data is phone acc data.  No baselining will be done\n";
    break;
  case Parameters::SensorType::AX3_ACCELEROMETER:
    cout << "Data is AX3 accelerometer data.\n";
    cout << "Input sample rate is ";
    if (sampleRateSet) {
     cout << getSampleRate() << " Hz\n";
    }
    else {
      cout << "to be determined from the data\n";
    }
    cout << "High pass filter cutoff frequency " <<
      getCutoff() << " Hz\n";
    break;

  case Parameters::SensorType::GPS_LOC:
  case Parameters::SensorType::LOCATION:
    cout << "Data is location data.\n";
    break;
    
  default:
    cerr << "Unsupported data type " <<
      static_cast<int>(getType()) << "\n";
    cerr << "Known sensors are " << knownSensors() << "\n";
    exit(EXIT_FAILURE);
  }
 
}


auto Parameters::getSampleRate() const -> double {
  if (!sampleRateSet) {
    throw new runtime_error("Sample rate not set yet");
  }
  return sampleRate;
}

