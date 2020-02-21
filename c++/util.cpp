/**
 * Various utility routines.
 *
 * Jason Leake October 2019
 */

#include "util.h"
#include <algorithm>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <iterator>
#include <sstream>
#include <sys/stat.h>
#include <sys/types.h>

using namespace std;
namespace fs = std::filesystem;

/**
 * Split string delimated by commas
 *
 * @param s string to split
 * @param delim delimator
 * @return vector of substrings
 */
auto util::split(const string& s, char delim) -> vector<string> {
  auto tokens = vector<string>{};
  auto token = string{};
  auto tokenStream = istringstream{s};
  while (getline(tokenStream, token, delim)) {
    tokens.push_back(ltrim(rtrim(token)));
  }
  return tokens;
}

/**
 * Trim leading whitespace from left hand side of a string
 *
 * @param str string to trim
 * @return trimmed string
 */
auto util::ltrim(const string& str) -> string {
  auto ret = str;
  constexpr auto sp = " \t\n\r\f\v";
  return ret.erase(0, ret.find_first_not_of(sp));
}

/**
 * Trim leading whitespace from right hand side of a string
 *
 * @param str string to trim
 * @return trimmed string
 */
auto util::rtrim(const string& str) -> string {
  auto ret = str;
  constexpr auto sp = " \t\n\r\f\v";
  return ret.erase(ret.find_last_not_of(sp) + 1);
}

/**
 * Check the specified file exists, displaying message
 * if it does not.
 *
 * @param filename filename to check
 * @return true if it exists
 */
auto util::exists(const string& filename) -> bool {
  if (!fs::exists(filename)) {
    cerr << filename << " -- File does not exist" << endl;
    return false;    
  }
  return true;
}


/**
 * Sanity check if the string parameter represents a floating point number
 *
 * @param field string variable to check
 * @param true if it is a number
 */
auto util::isNumber(const string& field) -> bool {
  for (auto index = size_t{0}; index < field.length(); index++) {
    auto ch = field[index];
    if (!isdigit(ch) && ch != '.' && ch != '-') {
      cerr << "Skipping non-numeric field " << field << endl;
      return false;
    }
  }
  return true; 
}


/**
 * Check if a CSV file has a header.  The header, if present, is
 * assumed to contain at least one field that starts with non-numeric
 * data, and the rest of the file is assumed to contain data that
 * always starts with numeric data
 *
 * @param filename name of CSV file to check
 * @param verbose set true to log whether header present to specified stream
 * @param stream stream to write diagnostic to
 * @return true if it has a header line at the start
 */
auto util::csvHasHeader(const fs::path& filename,
			bool verbose,
			ostream& stream) -> bool {
  auto file = ifstream{filename};
  auto line = string{};
  if (getline(file, line)) {
    auto ss = istringstream{line};
    auto vec = vector<string>{istream_iterator<string>(ss),
			      istream_iterator<string>()};
    for (auto&& val : vec) {
      auto iss = istringstream{val};
      auto number = 0.0;
      if (iss >> number) {
	// If we can write the stream into a numeric veriable then it
	// was a number
	continue;
      }
      else {
	// Otherwise it wasn't a valid number
	if (verbose) {
	  stream << "Header in " << filename << " is: " << line << endl;
	}
	// The first row isn't a list of numbers, so it must be a header
	return true;
      }
    }
  }
  else if (verbose) {
    stream << "Header absent" << endl;
  }
  return false;
}


/**
 * Make directories in path of specified file, so that the file itself can
 * then be created.
 *
 * @param outFilePath path of file
 */
auto util::makeDirectories(const fs::path& outFilePath) -> void {
  auto parent = outFilePath.parent_path();
  fs::create_directories(parent);
}


/**
 * Insert newlines into text string so that it is not printed as a
 * single long line, but broken up.
 *
 * @param stream stream to print processed string to
 * @param progname program name
 * @param text string to process
 */
auto util::justify(ostream& stream,
		   const string& progname,
		   const string& text) -> void {
  auto outstring = stringstream{progname};
  outstring << "\n\n";
  auto lineLength = 0ul;
  for_each(text.begin(), text.end(),
	   [&lineLength, &outstring] (const char& ch) {
	     switch (ch) {
	     case '\n':
	       lineLength = 0;
	       outstring << ch;
	       break;
	     default:
	       lineLength++;
	       outstring << ch;
	       if (lineLength > 60 && isspace(ch)) {
		 lineLength = 0;
		 outstring << "\n";
	       }
	     }
	   });
  outstring << "\n";
  // Output another newline AND flush.
  stream << outstring.str() << endl;
}

/**
 * Trim leading and trailing whitespace, and comments from line
 * read from file.
 *
 * @param str line read
 * @return trimmed line
 */
auto util::preprocessLine(const string& str) -> string {
  return rtrim(str.substr(0, str.find("#")));
}

/**
 * Return empty string. Used for methods and functions that return
 * string values when they have an error.
 *
 * @param source source code file
 * @param line source code line number
 */
auto util::errorReturnString(string source, int line) -> string {
  cerr << "Error return from " << source << " line " << line << endl;
  return "";
}

/**
 * Return string all converted to upper or lower case, and short cuts
 * for calling it.
 * 
 * @param str string to convert
 * @param upperCase true for uppercase, false for lowercase
 * @return converted string
 */
auto util::setCase(const string& str, bool upperCase) -> string {
  auto retval = str;
  transform(retval.begin(), retval.end(), retval.begin(),
	    [upperCase] (unsigned char ch) {
	      return upperCase ? toupper(ch) : tolower(ch);
	    });
  return retval;
}

auto util::locase(const string& str) -> string{
  return setCase(str, false);
}

auto util::upcase(const string& str) -> string {
  return setCase(str, true);
}

auto util::locase(const char* const str) -> string {
  return setCase(static_cast<string>(str), false);
}

auto util::upcase(const char* const str) -> string {
  return setCase(static_cast<string>(str), true);
}

/**
 * Print a general "all done" message and terminate the program
 *
 * @param success true for success, false for error
 * @param progName program name
 */
auto util::exit(bool success,
		const string& progName) -> void {
  auto message = success ? 
    " ALL DONE FOR THIS FILE " :
    " PROGRAM TERMINATING WITH AN ERROR ";
  cout << "\n" << util::repeat(20,'#') << " " << upcase(progName) << 
    message << util::repeat(20,'#') << "\n" << endl;
  std::exit(success ? EXIT_SUCCESS : EXIT_FAILURE);
}
