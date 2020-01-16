#pragma once
#include "Average.h"
#include <deque>

class RollingMean : public Average, private std::deque<double> {
private:
  unsigned long count = 0;
  size_t depth;
  double sum = 0;
  bool meanValid = false;

  auto calcSum() -> double;

public:
  RollingMean(size_t depth);
  virtual ~RollingMean() = default;

  
  virtual auto add(double val) -> void;
  
  virtual auto getAverage() -> double;
  
};

#endif
