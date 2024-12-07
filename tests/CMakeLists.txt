cmake_minimum_required(VERSION 3.19)

list(APPEND CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/cmake)
find_package(ESMF 8.0.0 MODULE REQUIRED)

project(ESMF-PERFORMANCE-TESTS
        VERSION 1.0
        LANGUAGES Fortran)

include(CTest)

add_subdirectory(hello_world)
add_subdirectory(esmf_initialize)
add_subdirectory(esmf_reconcile)
