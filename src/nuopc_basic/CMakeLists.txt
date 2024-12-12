add_executable(nuopc_basic app.F90
                           basic_driver.F90
                           nuopc_comp1.F90
                           nuopc_comp2.F90
)
target_link_libraries(nuopc_basic PUBLIC ESMF)
