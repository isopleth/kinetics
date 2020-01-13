/**
 * Square matrix, for gyroscope calculations.
 *
 * Jason Leake October 2019
 */

#pragma once

#include <iostream>
#include <ostream>

/**
 * Class encapsulates a 3x3 matrix
 */
class SquareMatrix {

private:
  // Column and row indices
  static constexpr const int ELEMENTS[3]{0, 1, 2};
  static constexpr const size_t ELEMENT_COUNT = 
    sizeof(ELEMENTS)/sizeof(ELEMENTS[0]);
    
  // The values in the matrix  
  double values[ELEMENT_COUNT][ELEMENT_COUNT];
  
public:
  
  SquareMatrix();
  virtual ~SquareMatrix() = default;

  auto trace() const -> double;
  auto setIdentity() -> void;
  auto set(size_t row, size_t col, double val) -> void;
  auto print(const char* const name,
	     std::ostream& outputStream= std::cout) -> void;
  auto operator*(const SquareMatrix& other) -> SquareMatrix;
};
