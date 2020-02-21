#pragma once

/**
 * Class for handling command line option descriptions. Just makes
 * it a bit quicker to write the runtime help.
 *
 * Jason Leake
 *
 * January 2020
 */
#include <string>
#include <vector>

class Option {
 private:
  // Short option
  std::string shortoption;
  // Long option
  std::string longoption;
  // Text description of what the option does
  std::string description;
  // Whether it has a parameter or not
  bool parameter;
  // If it is present by default
  bool enabledByDefault;
  
 public:
  Option(const std::string& shortoption,
	 const std::string& longoption,
	 const std::string& description,
	 bool parameter = false,
	 bool enabledByDefault = false) :
  shortoption(shortoption),
    longoption(longoption),
    description(description),
    parameter(parameter),
    enabledByDefault(enabledByDefault) {};
  virtual ~Option() = default;

  static auto show(const std::vector<Option>& options) -> void;
};
