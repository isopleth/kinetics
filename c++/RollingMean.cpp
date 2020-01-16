/**
 * Jason Leake October 2019
 */
#include "RollingMean.h"
using namespace std;
#include <iostream>

auto RollingMean::calcSum() -> double {
  auto sum = 0.;
  for (auto&& val : *this) {
    sum += static_cast<double>(val);
  }
  return sum;
}


RollingMean::RollingMean(size_t depth) : depth{depth} { }

  /**
   * Add a new value to the set of elements.  Discards the
   * least recently added element in the set if it has reached
   * its maximum size to make room for the new element.
   *
   * @param val value to add
   */
auto RollingMean::add(double val) -> void {
  push_back(val);

  if (size() > depth) {
    auto oldestElement = front();
    pop_front();
    if (oldestElement == val) {
      // Replacing oldest element with a value equal
      // to it, so no change
      meanValid = true;
      return;
    }
    else {
      sum = sum - oldestElement + val;
      meanValid = false;
    }
  }
  else {
    sum = sum + val;
    meanValid = false;
  }
}

/**
 * Get the mean value of the set
 *
 * @return mean value
 */
auto RollingMean::getAverage() -> double {
  constexpr decltype(count) CHECK_COUNT = 10000;
  // Mean of zilch is undefined
  if (empty()) {
    cerr << "Average required when there isn't one yet\n";
    cerr.flush();
    exit(EXIT_FAILURE);
  }
  
  // Check for drift in the running total at periodic intervals
  // To keep the computation speed up we modify the running total
  // each time a new element is added and an old one discarded.
  // It will drift after we do this lots of times because of
  // rounding errors etc. so have a check for this.
  count++;
  // Calculate the mean from the running total
  auto retval = sum / static_cast<double>(size());
  if (count % CHECK_COUNT == 0) {
    // Calculate the mean from scratch and compare it with the
    // mean calculated from the running total to make sure they
    // are the same.  If they aren't then emit an error message
    // and use the newly calculated mean
    auto calculatedSum = calcSum();
    auto recalulatedRetval = calculatedSum / static_cast<double>(size());
    if (retval != recalulatedRetval) {
      // If this ever happens we need to reduce CHECK_COUNT
      cerr << "Using recalculated mean at iteration " <<
	count << "!" <<endl;
      retval = recalulatedRetval;
    }
    // Refresh the sum with the newly calculated sum anyway
    // to get rid of tiny rounding errors which don't have an
    // effect on the mean yet.
    sum = calculatedSum;
  }
  return retval;
}


