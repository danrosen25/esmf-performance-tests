add_executable(esmf_reconcile app.F90 comp.F90)
target_link_libraries(esmf_reconcile PUBLIC ESMF)
