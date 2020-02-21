/**
 * Class for handling command line option descriptions.
 *
 * Jason Leake
 *
 * January 2020
 */

#include "Option.h"
#include <iostream>

using namespace std;

/**
 * Show the help associated with the options
 *
 * @param options vector of options
 */
auto Option::show(const vector<Option>& options) -> void {
  for (auto&& option : options) {
    cout << option.shortoption;
    if (option.parameter) {
      cout << " <val>";
    }
    cout << ", " << option.longoption;
    if (option.parameter) {
      cout << " <val>";
    }
    cout << "   " << option.description;
    if (option.enabledByDefault) {
      cout << " (default)";
    }
    cout << endl;
  }
}
