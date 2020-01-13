/**
 * This is the data structure used with STXXL.  A large number of these
 * are stored in STXXL.  Each one is a character string format datetime
 * and six double precision numbers.
 *
 * Jason Leake October 2019
 */

#include "Rows.h"

using namespace std;

/**
 * Allocate sufficient space to store the specifed number of rows
 * in the STXXL collection.
 *
 * @param size number of rows to allocate space for
 */
Rows::Rows(std::size_t size) {
  if (size > 0) {
    rows.reserve(size);
  }
}


/**
 * Convert Row object to RowData struct.  The Row object cannot be stored
 * in an STXXL collection, so we store a RowData version of it instead.
 *
 * @param row row to convert
 * @param rowdata struct to copy object into
 */
auto Rows::makeRowData(const Row& row,
		       RowData& rowdata) const -> void {
  for (auto index = size_t{0}; index < row.size(); index++) {
    rowdata.data[index] = row.at(index);
  }
  row.getDatetime().copy(rowdata.datetime, RowData::SIZE);
  rowdata.datetime[RowData::SIZE-1] = '\0';
}

/**
 * Convert rowdata struct back to a Row object
 *
 * @param rowData rowData struct to read
 * @return corresponding Row object
 */
auto Rows::makeRow(const RowData& rowData) const -> Row {
  return Row(static_cast<string>(rowData.datetime).substr(0,19),
	     rowData.data[0],
	     rowData.data[1],
	     rowData.data[2],
	     rowData.data[3],
	     rowData.data[4],
	     rowData.data[5]);		
}

/**
 * Get the number of rows stored in the STXXL collection.  Each row
 * corresponds to a single rowdata object.
 *
 * @return number of rows
 */
auto Rows::size() const -> std::size_t {
  return rows.size();
}

/**
 * Append a row of data to the STXXL collection.
 *
 * @param datetimein date time
 * @param x x acceleration or rotation value
 * @param y z acceleration or rotation value
 * @param z z acceleration or rotation value
 */
auto Rows::push_back(const string& datetimein,
		     double x, double y, double z) -> void {
  auto rowdata = RowData{};
  rowdata.data[0] = x;
  rowdata.data[1] = y;
  rowdata.data[2] = z;
  rowdata.data[3] = rowdata.data[4] =rowdata.data[5] = 0;  
  datetimein.copy(rowdata.datetime, RowData::SIZE);
  rowdata.datetime[RowData::SIZE-1]='\0';
  rows.push_back(rowdata);
}

/**
 * Append a row of data to the STXXL collection.
 *
 * @param datetimein date time
 * @param x x acceleration or rotation value
 * @param y z acceleration or rotation value
 * @param z z acceleration or rotation value
 */
auto Rows::push_back(const std::string& datetimein, double latitude,
		     double longitude, double altitude,
		     double accuracy, double speed) -> void {
  auto rowdata = RowData{};
  rowdata.data[0] = latitude;
  rowdata.data[1] =longitude;
  rowdata.data[2] = altitude;
  rowdata.data[3] = accuracy;
  rowdata.data[4] = speed;
  datetimein.copy(rowdata.datetime, RowData::SIZE);
  rowdata.datetime[RowData::SIZE-1]='\0';
  rows.push_back(rowdata);
}

/**
 * Put a row datum at a specified row index
 * @param rowIndex row number in the STXXL collection
 * @param dataType data type - RAW or COOKED. RAW accesses data index
 * 0-->2, and COOKED accesses 3-->5.  Used where the first thee values
 * hold the original data for the axes, and the last three hold
 * the corresponding processed values.
 * @param axis 0,1,2 for axis
 */
auto Rows::putValue(std::size_t index,
		    Row::DataType dataType,
		    size_t axis, double value) -> void {
  rows.at(index).data[3*static_cast<size_t>(dataType) + axis] = value;
}

/**
 * Get row datum at specified row index
 *
 * @param rowIndex row number in the STXXL collection
 * @param datumIndex which data value in the row [0:5]
 * @return datum value
 */
auto Rows::getValue(std::size_t rowIndex,
		    std::size_t datumIndex) -> double {
  return rows.at(rowIndex).data[datumIndex];
}

/**
 * Get row datum at specified row index
 *
 * @param rowIndex row number in the STXXL collection
 * @param dataType data type - RAW or COOKED. RAW accesses data index
 * 0-->2, and COOKED accesses 3-->5.  Used where the first thee values
 * hold the original data for the axes, and the last three hold
 * the corresponding processed values.
 * @param axis 0,1,2 for axis
 * @return datum value
 */
auto Rows::getValue(std::size_t index,
		    Row::DataType dataType,
		    size_t axis) -> double {
  return rows.at(index).data[3*static_cast<size_t>(dataType) + axis];
}

/**
 * Get date time as epoch value, at specified index
 *
 * @param index row index
 * @return number of seconds since 1/1/1970
 */
auto Rows::getSecond(std::size_t index) const -> unsigned long {
  return makeRow(rows.at(index)).getDatetimeEpoch();
}

/**
 * Get datetime of row at specified row index
 * @param index row index
 * @return date time as a string
 */
auto Rows::getDatetime(std::size_t index) -> std::string {
  return string{rows.at(index).datetime};
}

