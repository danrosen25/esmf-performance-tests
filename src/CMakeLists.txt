cmake_minimum_required(VERSION 3.19)

list(APPEND CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/cmake)
find_package(ESMF 8.0.0 MODULE REQUIRED)

project(ESMF-PERFORMANCE-TESTS
        VERSION 1.0
        LANGUAGES Fortran)

include(CTest)
find_package(MPI)

add_subdirectory(esmf_initialize)
add_subdirectory(esmf_reconcile)
add_subdirectory(esmx_basic)

file(GLOB_RECURSE TEST_INCLUDE_LIST "${CMAKE_CURRENT_BINARY_DIR}/testcfg/*.cmake")
foreach(TEST_INCLUDE IN LISTS TEST_INCLUDE_LIST)
  include(${TEST_INCLUDE})
endforeach()
