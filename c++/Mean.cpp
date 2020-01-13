/**
 * Jason Leake October 2019
 */

#include "Mean.h"
using namespace std;
#include <iostream>

/**
 * Get number of values accumulated so far
 *
 * @return number of values, N
 */
auto Mean::getCount() -> unsigned long {
  return count;
}

/**
 * Clear out all of the accumulated values
 */
auto Mean::reset() -> void {
  sum = 0;
  count = 0;
}

/**
 * Add a new value to the set of elements.
 *
 * @param val value to add
 */
auto Mean::add(double val) -> void {
  sum = sum + val;
  count++;
}

/**
 * Add a number of identical new values to the set of elements.
 *
 * @param val value to add
 * @param valCount how many times the value should be added
 */
auto Mean::addMultiple(double val, unsigned long valCount) -> void {
  sum = sum + (val * valCount);
  count += valCount;
}


/**
 * Get the mean value of the set
 *
 * @return mean value
 */
auto Mean::getAverage() -> double {
  // Mean of zilch is undefined
  if (count == 0) {
    cerr << "Average required when there isn't one yet\n";
    cerr.flush();
    exit(EXIT_FAILURE);
  }
  
  return sum/static_cast<double>(count);
}

