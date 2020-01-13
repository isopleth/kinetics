/**
 * Class used to store data for all of the file. STXXL compatible.
 *
 * Jason Leake October 2019
 */

#pragma once
#include "Row.h"

/**
 * STXXL can only handle plain old datatypes (PODs), and not fancy
 * classes that use pointers.  So convert Row to a POD called RowData
 * for storage and retrieval.  All a bit clunky but it works!
 */

#include <stxxl/vector>
#include <stxxl/bits/common/external_shared_ptr.h>

class Rows {

private:
  // This is the struct we store in the STXXL vector
  struct RowData {
    enum {SIZE = 30};
    char datetime[SIZE];
    // x,y,z for kinematic data, and then filtered versions added OR
    // latitude, longitude, altitude, accuracy, speed for location data
    double data[6];
  };
  
  stxxl::VECTOR_GENERATOR<RowData>::result rows;
  
  auto makeRowData(const Row& row,
		   RowData& rowdata) const -> void;
  
  auto makeRow(const RowData& rowData) const -> Row;
  
public:
  Rows(std::size_t size = 0);
  auto clear() -> void;
  auto size() const -> std::size_t;
  auto getSecond(std::size_t index) const -> unsigned long;
  auto getDatetime(std::size_t index) -> std::string;
  
  auto push_back(const std::string& datetime, double latitude,
		 double longitude, double altitude,
		 double accuracy, double speed) -> void;

  auto push_back(const std::string& datetime, double x,
		 double y, double z) -> void;

 
  auto putValue(std::size_t index,
		Row::DataType dataType,
		std::size_t axis, double value) -> void;
  
  auto getValue(std::size_t index,
		Row::DataType dataType,
		std::size_t axis) -> double;
  
  auto getValue(std::size_t rowIndex,
		std::size_t datumIndex) -> double;
  
};
