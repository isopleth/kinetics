/**
 * Reduce dataset size by subsampling.
 *
 * Jason Leake October 2019
 */

#pragma once

#include <filesystem>
#include "cleaner_files/Parameters.h"

/**
 * This class is a functor for reducing the amount of data by
 * aggregating all the values read in each second into a mean value
 * for that second.
 */

class Rows;

namespace cleaner {
  class Reduce {
  public:
    Reduce() = default;
    virtual ~Reduce() = default;
    
    auto reduce(const class cleaner::Parameters& parameters,
		Rows& rows,
		const std::filesystem::path& outFilePath) -> unsigned long;
    
    auto noreduce(const cleaner::Parameters& parameters,
		  Rows& rows,
		  const std::filesystem::path& outFilePath) -> unsigned long;

  };
}
