/**
 * Various utility routines. See corresponding .cpp for documentation.
 *
 * Jason Leake October 2019
 */
#pragma once

#include <filesystem>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace util {

  // String handling
  auto split(const std::string& s, char delim) -> std::vector<std::string>;

  auto ltrim(const std::string& str) -> std::string;

  auto rtrim(const std::string& str) -> std::string;

  auto setCase(const std::string& str, bool upperCase) -> std::string;
  

  auto locase(const char* const str) -> std::string;
  auto locase(const std::string& str) -> std::string;
  
  auto upcase(const char* const str) -> std::string;
  auto upcase(const std::string& str) -> std::string;

  auto isNumber(const std::string& field) -> bool;

  auto justify(std::ostream& stream,
	       const std::string& progname,
	       const std::string& text) -> void;

  /**
   * Convert string to numeric variable.
   * @param s string to convert
   * @param var variable to put converted string into
   * @return true if conversion successful, false on failure.
   */
  template<typename T> auto strtonum(const std::string& s, T& var) -> bool {
    std::istringstream iss(s);
    iss >> var;
    return !iss.fail();
  }

  /**
   * Create a string with the specified symbol repeated the specified
   * number of times.
   *
   * @param count number of repetitions
   * @param symbol to repeat
   */
  template<typename T> auto repeat(int count, const T& symbol) -> std::string {
    auto returnVal = std::stringstream{};
    for (auto index = 0; index < count; index++) {
      returnVal << symbol;
    }
    return returnVal.str();
  }

  auto errorReturnString(std::string source, int line) -> std::string;

  auto preprocessLine(const std::string& str) -> std::string;

  auto allDone(std::ostream& stream, const std::string& progname) -> void;
  
  // File handling
  
  auto csvHasHeader(const std::filesystem::path& filename,
		    bool verbose = true,
		    std::ostream& stream = std::cout) -> bool;

  auto exists(const std::string& filename) -> bool;
  
  auto makeDirectories(const std::filesystem::path& outFilePath) -> void;
  
}
