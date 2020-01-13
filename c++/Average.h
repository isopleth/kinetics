/**
 * Jason Leake October 2019
 */

#pragma once

/**
 * Interface for mean and median calculation classes
 */
class Average {
public:
  virtual void add(double value) = 0;
  virtual double getAverage() = 0;
  virtual unsigned long getCount() = 0;
};

