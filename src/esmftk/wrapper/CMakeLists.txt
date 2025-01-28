cmake_minimum_required(VERSION 3.19)

project(ESMFTK
        VERSION 1.0
)

include(CTest)

find_package(MPI)

if(DEFINED ESMFTK_TESTS_SRC)
  add_subdirectory(${ESMFTK_TESTS_SRC} testsrc)
  unset(ESMFTK_TESTS_SRC CACHE)
endif()

file(GLOB_RECURSE TEST_INCLUDE_LIST "${CMAKE_CURRENT_BINARY_DIR}/testcfg/*.cmake")
foreach(TEST_INCLUDE IN LISTS TEST_INCLUDE_LIST)
  include(${TEST_INCLUDE})
endforeach()
