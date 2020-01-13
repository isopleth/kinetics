/**
 * Parameters controlling program operation.
 *
 * Jason Leake October 2019
 */

#pragma once
#include "SensorParameter.h"
#include <map>
#include <string>

namespace cleaner {
  class Parameters : public SensorParameter {
    
  private:
    const bool detectRate; // True if the program is to determine sample rate
    bool sampleRateSet;
    double sampleRate; // Input file data sample rate
    const double cutoff;     // Cutoff in Hertz. 0.05 Hz

    const bool forceFileRegeneration;
    
  public:
    Parameters(bool detectSampleRate,
	       double sampleRate,
	       double cutoff,
	       const std::string& typeString,
	       bool forceFileRegeneration);
    
    auto setSampleRate(double rate) { sampleRateSet = true; sampleRate = rate; }
    auto detectSampleRate() const { return detectRate; }
    auto alwaysRegenerateFile() const { return forceFileRegeneration; }
    auto getCutoff() const { return cutoff; }
    auto getSampleRate() const -> double;
    auto show() const -> void;  
  };
}
