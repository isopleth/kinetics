/**
 * Encapsulates a single row read from data file.
 *
 * Jason Leake October 2019
 */

#pragma once

#include <array>
#include <string>
#include "SensorParameter.h"

namespace Rowcons {
  static constexpr auto COLUMNS = 6;
}

class Row : public std::array<double, Rowcons::COLUMNS> {

private:
  static constexpr auto QUANTUM = 0.015625;
  std::string datetime;

  static constexpr auto LOCATION_HEADER = "datetime, epoch, latitude, longitude, altitude, accuracy, speed\r\n";
  static constexpr auto KINETIC_HEADER = "datetime, epoch, x, y, z, total\r\n";
  static constexpr auto KINETIC_PLUS_HEADER =  "datetime, epoch, x, y, z, total, xfilt, yfilt, zfilt, totalfilt\r\n";

  auto getDateTimeMillis() const -> unsigned long;
  
public:
  Row();
  
  enum class DataType { RAW = 0,
			COOKED = 1};

  auto getDatetime() const -> std::string;
  auto getDatetimeEpoch(bool millisecondsEpoch) const -> unsigned long;

  Row(const std::string& datetime,
      const double x,
      const double y,
      const double z);

  Row(const std::string& datetime,
      const double x1,
      const double y1,
      const double z1,
      const double x2,
      const double y2,
      const double z2 = 0);

  static auto heading(const SensorParameter& sensor) -> std::string;

  static auto writeLocationRecord(std::ofstream& stream,
				  const std::string& datetime,
				  const unsigned long& epoch,
				  const double& latitude,
				  const double& longitude,
				  const double& altitude,
				  const double& accuracy,
				  const double& speed) -> void;

  static auto getLocationHeader() -> std::string;

  auto toString(const SensorParameter& parameters,
		bool millisecondsEpoch) const -> std::string;
  
private:
  auto truncate(int val, unsigned bitmask) -> int;

  auto sstringValues(std::stringstream& sstream,
		     unsigned long count,
		     const SensorParameter& sensor) const -> void;

  auto sstringValues(std::stringstream& sstream,
		     const SensorParameter& sensor,
		     DataType dataType) const -> void;

  static auto quantize(double value) -> int;

  auto putValue(DataType dataType,
		size_t axis, double value) -> void;

  static auto totalRotation(double x, double y, double z) -> double;
  static auto toDegrees(double radians) -> double;
};


