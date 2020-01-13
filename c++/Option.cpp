
/**
 * Class for handing command line option descriptions.
 *
 * Jason Leake
 *
 * January 2020
 */

#include "Option.h"
#include <iostream>

using namespace std;

/**
 * Show the help associated with this option
 */
auto Option::show(const std::vector<Option>& options) -> void {
  for (auto&& option: options) {
    cout << option.shortoption;
    if (option.parameter) {
      cout << " <val>";
    }
    cout << ", " << option.longoption;
    if (option.parameter) {
      cout << " <val>";
    }
    cout << "   " << option.description;
    if (option.def) {
      cout << " (default)";
    }
    cout << endl;
  }
}
