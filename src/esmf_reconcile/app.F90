!==============================================================================
! Earth System Modeling Framework
! Copyright (c) 2002-2024, University Corporation for Atmospheric Research,
! Massachusetts Institute of Technology, Geophysical Fluid Dynamics
! Laboratory, University of Michigan, National Centers for Environmental
! Prediction, Los Alamos National Laboratory, Argonne National Laboratory,
! NASA Goddard Space Flight Center.
! Licensed under the University of Illinois-NCSA License.
!==============================================================================

!> ESMF Reconcile Test
program esmf_reconcile_test
  ! modules
  use ESMF
  use Comp, only: compSS => SetServices

  implicit none

  ! local variables
  integer                :: rc, urc, unit
  integer                :: i, j
  integer                :: petCount, localPet
  integer                :: compCount
  type(ESMF_GridComp), allocatable :: compList(:)
  integer, allocatable   :: petList(:)
  character(ESMF_MAXSTR) :: configfile, compid
  type(ESMF_VM)          :: vm
  type(ESMF_Config)      :: config, configComp
  type(ESMF_State)       :: state
  real(ESMF_KIND_R8)     :: begTime, endTime, totTime
  real(ESMF_KIND_R8)     :: localTime(1), maxTime(1)
  real(ESMF_KIND_R8)     :: fastestTestTime
  real(ESMF_KIND_R8)     :: globalMaxTime
  real(ESMF_KIND_R8)     :: petListBoundsRel(2)
  integer                :: argCount
  integer, parameter     :: numTests=5

  ! initialize ESMF
  call ESMF_Initialize(vm=vm, rc=rc)
  if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
    line=__LINE__, file=__FILE__)) &
    call ESMF_Finalize(endflag=ESMF_END_ABORT)
  call ESMF_LogWrite("esmf_reconcile_test STARTING", ESMF_LOGMSG_INFO, rc=rc)
  if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
    line=__LINE__, file=__FILE__)) &
    call ESMF_Finalize(endflag=ESMF_END_ABORT)
  call ESMF_VMGet(vm, petCount=petCount, localPet=localPet, rc=rc)
  if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
    line=__LINE__, file=__FILE__)) &
    call ESMF_Finalize(endflag=ESMF_END_ABORT)

  ! load config file from command line arguments
  if (localPet .eq. 0) then
    call ESMF_UtilGetArgC(argCount, rc=rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=__LINE__, file=__FILE__)) &
      call ESMF_Finalize(endflag=ESMF_END_ABORT)
    if (argCount .gt. 0) then
      call ESMF_UtilGetArg(argindex=1, argvalue=configfile, rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) &
        call ESMF_Finalize(endflag=ESMF_END_ABORT)
    else
      if (localPet == 0) then
        write(*,*) "ERROR: Config file name must be supplied as an"// &
                   " argument on the command line."
      end if
      call ESMF_LogSetError(rcToCheck=ESMF_RC_ARG_BAD, &
        msg="Application must be called with the name of the config"// &
            " file as the only argument on the command line.", &
          line=__LINE__, file=__FILE__, rcToReturn=rc)
      call ESMF_Finalize(endflag=ESMF_END_ABORT)
    end if
  end if
  call ESMF_VMBroadcast(vm, configfile, ESMF_MAXSTR, rootPet=0, rc=rc)
  if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
    line=__LINE__, file=__FILE__)) &
    call ESMF_Finalize(endflag=ESMF_END_ABORT)
  config = ESMF_ConfigCreate(rc=rc)
  if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
    line=__LINE__, file=__FILE__)) &
    call ESMF_Finalize(endflag=ESMF_END_ABORT)
  call ESMF_ConfigLoadFile(config, configfile, rc=rc)
  if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
    line=__LINE__, file=__FILE__)) &
    call ESMF_Finalize(endflag=ESMF_END_ABORT)

  ! read compCount
  call ESMF_ConfigGetAttribute(config, label="compCount:", &
    value=compCount, rc=rc)
  if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
    line=__LINE__, file=__FILE__)) &
    call ESMF_Finalize(endflag=ESMF_END_ABORT)
  allocate(compList(compCount))

  ! reconcile tests loop
  fastestTestTime = HUGE(fastestTestTime)
  do j = 1, numTests
    ! add component to compList
    do i = 1, compCount
      write(compid,"('comp-',I2.2)") i
      configComp = ESMF_ConfigCreate(config, &
        openlabel="<"//trim(compid)//":", &
        closelabel=":"//trim(compid)//">", &
        rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) &
        call ESMF_Finalize(endflag=ESMF_END_ABORT)
      call get_comp_petlist(configComp, petList=petList, rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) &
        call ESMF_Finalize(endflag=ESMF_END_ABORT)
      if (localPet==0) then
        write(*,*) trim(compid), " PetList=", petList
      end if
      call ESMF_LogWrite("Creating '"//trim(compid)//"' component.", &
        ESMF_LOGMSG_INFO, rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) &
        call ESMF_Finalize(endflag=ESMF_END_ABORT)
      compList(i) = ESMF_GridCompCreate(name=trim(compid), config=configComp, &
        petList=petList, rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) &
        call ESMF_Finalize(endflag=ESMF_END_ABORT)
      deallocate(petList)

      ! set services for compList
      call ESMF_GridCompSetServices(compList(i), userRoutine=compSS, &
        userRc=urc, rc=rc)
      if (ESMF_LogFoundError(rcToCheck=urc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) &
        call ESMF_Finalize(endflag=ESMF_END_ABORT)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) &
        call ESMF_Finalize(endflag=ESMF_END_ABORT)
     end do ! addcomp(i)

     ! initialize components with shared state
     state = ESMF_StateCreate(name="State", rc=rc)
     if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
       line=__LINE__, file=__FILE__)) &
       call ESMF_Finalize(endflag=ESMF_END_ABORT)
     do i = 1, compCount
       call ESMF_GridCompInitialize(compList(i), phase=1, importState=state, &
         userRc=urc, rc=rc)
       if (ESMF_LogFoundError(rcToCheck=urc, msg=ESMF_LOGERR_PASSTHRU, &
         line=__LINE__, file=__FILE__)) &
         call ESMF_Finalize(endflag=ESMF_END_ABORT)
       if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
         line=__LINE__, file=__FILE__)) &
         call ESMF_Finalize(endflag=ESMF_END_ABORT)
     end do ! initcomp(i)

     ! initialize timing and memory measurements
     call ESMF_VMBarrier(vm, rc=rc)
     if (ESMF_LogFoundError(rcToCheck=urc, msg=ESMF_LOGERR_PASSTHRU, &
       line=__LINE__, file=__FILE__)) &
       call ESMF_Finalize(endflag=ESMF_END_ABORT)
     call ESMF_VMLogMemInfo(prefix="before Reconcile", rc=rc)
     if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
       line=__LINE__, file=__FILE__)) &
       call ESMF_Finalize(endflag=ESMF_END_ABORT)
     call ESMF_TraceRegionEnter("Reconcile", rc=rc)
     if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
       line=__LINE__, file=__FILE__)) &
       call ESMF_Finalize(endflag=ESMF_END_ABORT)
     call ESMF_VMWTime(begtime, rc=rc)
     if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
       line=__LINE__, file=__FILE__)) &
       call ESMF_Finalize(endflag=ESMF_END_ABORT)

     ! call state reconcile
     call ESMF_StateReconcile(state, rc=rc)
     if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
       line=__LINE__, file=__FILE__)) &
       call ESMF_Finalize(endflag=ESMF_END_ABORT)

     ! finalize timing and memory measurement
     call ESMF_VMWTime(endTime, rc=rc)
     if (ESMF_LogFoundError(rcToCheck=urc, msg=ESMF_LOGERR_PASSTHRU, &
       line=__LINE__, file=__FILE__)) &
       call ESMF_Finalize(endflag=ESMF_END_ABORT)
     call ESMF_TraceRegionExit("Reconcile", rc=rc)
     if (ESMF_LogFoundError(rcToCheck=urc, msg=ESMF_LOGERR_PASSTHRU, &
       line=__LINE__, file=__FILE__)) &
       call ESMF_Finalize(endflag=ESMF_END_ABORT)
     call ESMF_VMLogMemInfo(prefix="after Reconcile", rc=rc)
     if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
       line=__LINE__, file=__FILE__)) &
       call ESMF_Finalize(endflag=ESMF_END_ABORT)

     ! calculate state reconcile time
     localTime(1)=endTime-begTime
     call ESMF_VMReduce(vm, localTime, maxTime, 1, ESMF_REDUCE_MAX, 0, rc=rc)
     if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
       line=__LINE__, file=__FILE__)) &
       call ESMF_Finalize(endflag=ESMF_END_ABORT)
     ! calculated fastest test time
     if (maxTime(1) < fastestTestTime) fastestTestTime=maxTime(1)

     ! destroy components and shared state
     do i = 1, compCount
       call ESMF_GridCompDestroy(compList(i), rc=rc)
       if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
         line=__LINE__, file=__FILE__)) &
         call ESMF_Finalize(endflag=ESMF_END_ABORT)
     end do ! destroycomps(i)
     call ESMF_StateDestroy(state, rc=rc)
     if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
       line=__LINE__, file=__FILE__)) &
       call ESMF_Finalize(endflag=ESMF_END_ABORT)

  end do ! looptests(j)

  ! write out fastest time
  if (localPet == 0) then
    write(*,*) "For case ", trim(configfile), " on ", petCount, &
               " procs, the min reconcile time =",fastestTestTime
  end if

  ! finalize ESMF
  call ESMF_LogWrite("esmf_reconcile_test FINISHED", ESMF_LOGMSG_INFO, rc=rc)
  if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
    line=__LINE__, file=__FILE__)) &
    call ESMF_Finalize(endflag=ESMF_END_ABORT)
  call ESMF_Finalize(rc=rc)
  if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
    line=__LINE__, file=__FILE__)) &
    call ESMF_Finalize(endflag=ESMF_END_ABORT)

 !------------------------------------------------------------------------------
 contains
 !------------------------------------------------------------------------------

  subroutine create_petlist(petListBounds, petList)
    ! arguments
    integer, intent(in)               :: petListBounds(2)
    integer, allocatable, intent(out) :: petList(:)

    ! local variables
    integer :: petCount, i

    petCount = petListBounds(2) - petListBounds(1) + 1
    if (petCount < 0) petCount = 0

    allocate(petList(petCount))

    do i=1, petCount
      petList(i) = petListBounds(1) + i - 1
    enddo
  end subroutine

  subroutine get_comp_petlist(configComp, petList, rc)
    ! arguments
    type(ESMF_Config), intent(inout)  :: configComp
    integer, allocatable, intent(out) :: petList(:)
    integer, intent(out)              :: rc

    ! local variables
    integer(ESMF_KIND_I4) :: petListBounds(2)
    real(ESMF_KIND_R8)    :: petListBoundsRel(2)
    integer, parameter    :: badPet = -1

    rc = ESMF_SUCCESS

    ! use absolute bounds
    call ESMF_ConfigGetAttribute(configComp, valueList=petListBounds, &
      label="petListBounds:", default=badPet, rc=rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=__LINE__, file=__FILE__)) return

    ! use relative bounds
    if (petListBounds(1) == badPet) then
      call ESMF_ConfigGetAttribute(configComp, valueList=petListBoundsRel, &
        label="petListBoundsRel:", rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) return
      petListBounds(1) = INT(petListBoundsRel(1) * REAL(petCount))
      petListBounds(2) = INT(petListBoundsRel(2) * REAL(petCount))-1
    end if

    call create_petlist(petListBounds, petList)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=__LINE__, file=__FILE__)) return
  end subroutine get_comp_petlist

#if 0
subroutine check_state(state, config, isOk, rc)
  type(ESMF_Config)    :: config
  type(ESMF_State)     :: state
  logical              :: isOk
  integer, intent(out) :: rc

  integer                :: i, compCount
  character(ESMF_MAXSTR) :: compid
  type(ESMF_Config)      :: configComp

  rc = ESMF_SUCCESS
  isOk = .true.

  ! check component configuration
  call ESMF_ConfigGetAttribute(config, label="compCount:", value=compCount, &
    rc=rc)
  if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
       line=__LINE__, file=__FILE__) return
  do i = 1, compCount
    write(compid,"('comp-',I2.2)") i
    configComp = ESMF_ConfigCreate(config, &
      openlabel="<"//trim(compid)//":", &
      closelabel=":"//trim(compid)//">", &
      rc=rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=__LINE__, file=__FILE__)) return
  end do ! checkcomps(i)
end subroutine check_state
#endif

end program esmf_reconcile_test
