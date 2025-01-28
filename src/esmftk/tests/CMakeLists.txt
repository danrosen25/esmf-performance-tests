cmake_minimum_required(VERSION 3.19)

list(APPEND CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/cmake)
find_package(ESMF 8.0.0 MODULE REQUIRED)

set(CMAKE_Fortran_COMPILER "${ESMF_F90COMPILER}")
set(CMAKE_Fortran_FLAGS    "${ESMF_F90COMPILEOPTS}")

project(ESMF-PERFORMANCE-TESTS
        VERSION 1.0
        LANGUAGES Fortran)

find_package(MPI REQUIRED COMPONENTS Fortran)

add_subdirectory(esmf_initialize)
add_subdirectory(esmf_reconcile)
add_subdirectory(esmx_basic)
add_subdirectory(nuopc_basic)
