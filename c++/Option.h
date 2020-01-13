#pragma once

/**
 * Class for handing command line option descriptions.
 *
 * Jason Leake
 *
 * January 2020
 */
#include <string>
#include <vector>

class Option {
 private:
  std::string shortoption;
  std::string longoption;
  std::string description;
  bool parameter;
  bool def;
  
 public:
  Option(const std::string& shortoption,
	 const std::string& longoption,
	 const std::string& description,
	 bool parameter = false,
	 bool def = false) :
  shortoption(shortoption),
    longoption(longoption),
    description(description),
    parameter(parameter),
    def(def) {};
  virtual ~Option() = default;

  static auto show(const std::vector<Option>& ) -> void;
};
