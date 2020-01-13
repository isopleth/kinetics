/**
 * Square matrix, for gyroscope calculations.
 *
 * Jason Leake October 2019
 */

#include "SquareMatrix.h"

using namespace std;

/**
 * Constructor, initialises matrix to all zeroes
 */
SquareMatrix::SquareMatrix() {
  for (auto& row : ELEMENTS) {
    for (auto& col : ELEMENTS) {
      values[row][col] = 0;
    }
  }
}

/**
 * Generate the trace of the matrix - i.e. the sum of the
 * leading diagonal.
 *
 * @return the trace
 */
auto SquareMatrix::trace() const -> double {
  auto theTrace = double{0};
  for (auto& index : ELEMENTS) {
    theTrace += values[index][index];
  }
  return theTrace;
}

/**
 * Set the matrix to the identity matrix - i.e. with the
 * leading diagonal set to 1 and everything else as 0.
 */
auto SquareMatrix::setIdentity() -> void {
  for (auto& row : ELEMENTS) {
    for (auto& col : ELEMENTS) {
      values[row][col] = row ==  col ? 1 : 0;      
    }
  }
}

/**
 * Set specified element to given value
 *
 * @param row element row
 * @param col element column
 * @param val new value for element
 */
auto SquareMatrix::set(size_t row, size_t col, double val) -> void {
  values[row][col] = val;
}

/**
 * Print out the matrix.
 *
 * @param name name of the matrix
 */
auto SquareMatrix::print(const char* const name,
			 ostream& outputStream) -> void {
  outputStream << name << endl;
  for (auto& row : ELEMENTS) {
    outputStream << 
      values[row][0] << " " <<
      values[row][1] << " " <<
      values[row][2] << endl;
  }
}

/**
 * Multiply this matrix by another one
 *
 * @param other matrix
 * @return result of multiplication
 */
auto SquareMatrix::operator*(const SquareMatrix& other) -> SquareMatrix {
  auto newMatrix = SquareMatrix{};
  
  for (auto& row: ELEMENTS) {
    for (auto& column: ELEMENTS) {
      for (auto& rc: ELEMENTS) {
	newMatrix.values[row][column] +=
	  values[row][rc] * other.values[rc][column];
      }
    }
  }
  
  return newMatrix;
}
