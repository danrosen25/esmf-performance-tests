add_executable(esmf_reconcile app.F90 comp.F90)
target_link_libraries(esmf_reconcile PUBLIC ESMF)

add_test(NAME esmf_reconcile COMMAND esmf_reconcile "${CMAKE_CURRENT_SOURCE_DIR}/total_overlap.config")
