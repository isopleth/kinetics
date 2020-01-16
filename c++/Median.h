/**
 * Jason Leake October 2019
 */

#pragma once
#include "Average.h"
#include <vector>
#include <list>
#include <cmath>

/**
 * Median filter
 */
class Median : public Average, private std::vector<double> {
private:
  std::list<double> valuesByAge;
  size_t window;
  double medianValue;
  bool medianValid = false;
  
public:
  Median(size_t window);
  virtual ~Median() = default;

  auto getCount() -> unsigned long;
  auto add(double value) -> void;
  
  /**
   * Return the current median
   */
  auto getAverage() -> double;
 
};


