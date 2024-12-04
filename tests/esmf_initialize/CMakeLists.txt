add_executable(esmf_initialize app.F90)
target_link_libraries(esmf_initialize PUBLIC ESMF)

add_test(NAME esmf_initialize COMMAND esmf_initialize)
