/**
 * Jason Leake October 2019
 */

#include "Median.h"

#include <iostream>
#include <list>
#include <vector>
#include <algorithm>
#include <cassert>
using namespace std;

Median::Median(size_t window) : window(window) {
  reserve(window);
}
  
auto Median::getCount() -> unsigned long {
  return window;
}

auto Median::add(double value) -> void {
  if (isnan(value)) {
    throw runtime_error("Not a number");
  }
  
  if (size() < window) {
    push_back(value);
    valuesByAge.push_back(value);
    // Invalidate the median
    medianValid = false;
  }
  else {
    // Replace the oldest value in vector with the new value
    auto oldestValue = valuesByAge.front();
    // If the new value is the same as the oldest there is nothing
    // to do
    if (value == oldestValue) {
      return;
    }
    
    // Else replace the oldest value with the new value
    auto it = find(begin(), end(), oldestValue);
    if (it == end()) {
      cerr << "Value not in vector!\n"
	"Looking for " << value << "\n"
	"Sizes are " << size() << " and " << valuesByAge.size()
	   << endl;
      for (auto&& v: *this) {
	cerr << v << endl;
      }
      cerr << "---" << endl;
      for (auto&& v: valuesByAge) {
	cerr << v << endl;
      }
      cerr.flush();
      exit(EXIT_FAILURE);
    }
    else {
      *it = value;
    }
    valuesByAge.pop_front();
    valuesByAge.push_back(value);
    medianValid = false;
    
  }
}

/**
 * Return the current median
 */
auto Median::getAverage() -> double {
  assert(!empty());
  if (!medianValid) {
    // unsigned integer type divides rounds down.  It's an unsigned long
    // type anyway but cast to make it clear.
    auto halfSize = static_cast<unsigned long>((size() / 2));
    if (size() % 2 == 0) {
      // e.g. vec = [0..9], we woud want elements [4] and [5]
      // In this case, size = 10.  elements = [size/2] and [size/2 - 1]
      
      const auto rightMedianIt = begin() + halfSize;
      const auto leftMedianIt = rightMedianIt - 1;
      // This will partially reorder vec
      nth_element(begin(), leftMedianIt , end());
      const auto leftMedian = *leftMedianIt;
      // This will partically reorder vec again
      nth_element(begin(), rightMedianIt , end());
      const auto rightMedian = *rightMedianIt;
      medianValue = (leftMedian + rightMedian) / 2.;
    } else {
      // Odd number of elements.  If size = 11 we want element
      // 5
      const auto medianIt = begin() + halfSize;
      nth_element(begin(), medianIt , end());
      medianValue = *medianIt;
    }
    // Now that we have calculated the median, it is valid
    medianValid = true;
  }
  return medianValue;
} 
