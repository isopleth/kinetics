/**
 * Jason Leake October 2019
 */
#pragma once

#include "SensorParameter.h"
#include <iostream>
#include <vector>

class PhoneDataConverter {
private:
  
  SensorParameter::SensorType type;
  auto toStandardGravity(const std::string& value) -> std::string;
  static const std::string ERROR_RETURN_STRING;
  
public:
  
  PhoneDataConverter(const std::string& searchString);
  virtual ~PhoneDataConverter() {}
  
  auto match(const std::string& line) const -> bool;
  
  auto getType() const -> SensorParameter::SensorType;
  auto getTypeString() const -> std::string;
  
  auto convert(const std::string& line, size_t lineNumber) -> std::string;
  
  static auto countLines(const std::string& filename) -> int;

  static auto convertDatetime(const std::string& datetime) -> std::string;

  auto processKinematic(const std::vector<std::string>& fields,
			const std::string& line,
			size_t lineNumber) -> std::string;

  auto processGenericLocation(const std::vector<std::string>& fields,
			      const std::string& line,
			      size_t lineNumber) -> std::string;

  auto processSpecificLocation(const std::vector<std::string>& fields,
			       const std::string& line,
			       size_t lineNumber) -> std::string;
  
};


