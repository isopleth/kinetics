/**
 * Simple class wrapping up mean calculations
 *
 * Jason Leake October 2019
 */

#pragma once

#include "Average.h"

/**
 * Calculate mean of a fixed length set of values.  Once
 * the set has reached its maximum defined size, adding a
 * new element causes the oldest to be discarded.
 */
class Mean : public Average {
private:
  unsigned long count = 0;
  double sum = 0;

public:
  Mean() = default;
  virtual ~Mean() = default;
  
  auto getCount() -> unsigned long;
  auto reset() -> void;

  auto addMultiple(double val, unsigned long count) -> void;
  
  /**
   * Add a new value to the set of elements.  Discards the
   * least recently added element in the set if it has reached
   * its maximum size to make room for the new element.
   *
   * @param val value to add
   */
  virtual auto add(double val) -> void;
  
  /**
   * Get the mean value of the set
   *
   * @return mean value
   */
  virtual auto getAverage() -> double;
  
};


