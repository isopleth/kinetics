#pragma once

#include <map>
#include <string>

class SensorParameter {
 public:
  enum class SensorType {
			 PHONE_GYROSCOPE,
			 PHONE_ACCELEROMETER,
			 AX3_ACCELEROMETER,
			 LOCATION,
			 GPS_LOC };

  static std::map<std::string, SensorType> mapping;
  
  static constexpr const char* DEFAULT_TYPE_STRING = "ax3";
  
protected:
  SensorParameter(const std::string& type);
  
private:
  SensorType type;
  static auto generateMapping() -> void;
  
public:
  SensorParameter(SensorType type);
  virtual ~SensorParameter() = default;
  static auto knownSensors() -> std::string;
  auto isGyro() const -> bool;
  auto isLocation() const -> bool;
  auto isAcceleration() const -> bool;
  auto getType() const { return type; }
};
