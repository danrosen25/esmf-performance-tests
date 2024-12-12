!==============================================================================
! Earth System Modeling Framework
! Copyright (c) 2002-2024, University Corporation for Atmospheric Research,
! Massachusetts Institute of Technology, Geophysical Fluid Dynamics
! Laboratory, University of Michigan, National Centers for Environmental
! Prediction, Los Alamos National Laboratory, Argonne National Laboratory,
! NASA Goddard Space Flight Center.
! Licensed under the University of Illinois-NCSA License.
!==============================================================================

module comp
  ! modules
  use ESMF
  use NUOPC

  implicit none

  private

#define COMP_DEBUG_OUTPUT 0

  type FieldList
    type(ESMF_Field), pointer :: fieldList(:)
  end type FieldList

  type FieldListWrap
    type(FieldList), pointer :: wrap
  end type FieldListWrap

  type GridWrap
    type(ESMF_Grid), pointer :: wrap
  end type GridWrap

  type MeshWrap
    type(ESMF_Mesh), pointer :: wrap
  end type MeshWrap

  public SetServices

  !-----------------------------------------------------------------------------
  contains
  !-----------------------------------------------------------------------------

  subroutine SetServices(comp, rc)
    ! arguments
    type(ESMF_GridComp)  :: comp
    integer, intent(out) :: rc

    rc = ESMF_SUCCESS

    call ESMF_GridCompSetEntryPoint(comp, ESMF_METHOD_INITIALIZE, &
      phase=1, userRoutine=comp_init, rc=rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=__LINE__, file=__FILE__)) return

  end subroutine SetServices

  !-----------------------------------------------------------------------------

  subroutine comp_init(comp, importState, exportState, clock, rc)
    ! arguments
    type(ESMF_GridComp)   :: comp
    type(ESMF_State)      :: importState, exportState
    type(ESMF_Clock)      :: clock
    integer, intent(out)  :: rc

    ! local variables
    type(ESMF_Config)     :: config
    type(ESMF_Container)  :: fieldListContainer
    type(ESMF_Container)  :: gridContainer
    type(ESMF_Container)  :: meshContainer

    rc = ESMF_SUCCESS

    ! create containers to track already created objects
    fieldListContainer = ESMF_ContainerCreate(rc=rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=__LINE__, file=__FILE__)) return
    gridContainer = ESMF_ContainerCreate(rc=rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=__LINE__, file=__FILE__)) return
    meshContainer = ESMF_ContainerCreate(rc=rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=__LINE__, file=__FILE__)) return

    ! ingest the Config file, and populate the importState
    call ESMF_GridCompGet(comp, config=config, rc=rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=__LINE__, file=__FILE__)) return
    call add_state_members(importState, config, "stateMembers:", &
      fieldListContainer, gridContainer, meshContainer, rc=rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=__LINE__, file=__FILE__)) return

  end subroutine comp_init

  !-----------------------------------------------------------------------------

  recursive subroutine add_state_members(state, config, label, &
    fieldListContainer, gridContainer, meshContainer, rc)
    ! arguments
    type(ESMF_State)      :: state
    type(ESMF_Config)     :: config
    character(*)          :: label
    type(ESMF_Container)  :: fieldListContainer
    type(ESMF_Container)  :: gridContainer
    type(ESMF_Container)  :: meshContainer
    integer, intent(out)  :: rc

    ! local variables
    integer                     :: count, i
    character(40), allocatable  :: stateMembers(:)
    character(ESMF_MAXSTR), pointer :: tokenList(:)

    rc = ESMF_SUCCESS

    ! read state members
    count = ESMF_ConfigGetLen(config, label=label, rc=rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=__LINE__, file=__FILE__)) return
    allocate(stateMembers(count))
    call ESMF_ConfigGetAttribute(config, label=label, &
      valueList=stateMembers, rc=rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=__LINE__, file=__FILE__)) return

    ! loop over state members, tokenize, and populate importState
    do i = 1, count
      nullify(tokenList)
      call NUOPC_ChopString(stateMembers(i), chopChar="-", &
        chopStringList=tokenList, rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) return
      if (size(tokenList) /= 2) then
        call ESMF_LogSetError(ESMF_RC_ARG_BAD, &
          msg="Format problem in stateMember", &
          line=__LINE__, file=__FILE__, rcToReturn=rc)
        return
      end if
      if (tokenList(1) == "fields") then
        call add_fields(state, config, stateMembers(i), &
          fieldListContainer, gridContainer, meshContainer, rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=__LINE__, file=__FILE__)) return
      else if (tokenList(1) == "nest") then
        call add_nest(state, config, stateMembers(i), &
          fieldListContainer, gridContainer, meshContainer, rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=__LINE__, file=__FILE__)) return
      else
        call ESMF_LogSetError(ESMF_RC_ARG_BAD, &
          msg="stateMember is neither 'fields' nor 'nest'", &
          line=__LINE__, file=__FILE__, rcToReturn=rc)
        return
      end if
      if (associated(tokenList)) deallocate(tokenList)
    end do ! addmembers(i)

  end subroutine add_state_members

  !-----------------------------------------------------------------------------

  recursive subroutine add_nest(state, config, label, &
    fieldListContainer, gridContainer, meshContainer, rc)
    ! arguments
    type(ESMF_State), intent(inout) :: state
    type(ESMF_Config),intent(in)    :: config
    character(*),     intent(in)    :: label
    type(ESMF_Container)  :: fieldListContainer
    type(ESMF_Container)  :: gridContainer
    type(ESMF_Container)  :: meshContainer
    integer,          intent(out)   :: rc

    ! local variables
    type(ESMF_State)            :: nestedState

    rc = ESMF_SUCCESS

    ! create the nestedState
    nestedState = ESMF_StateCreate(name=label, rc=rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=__LINE__, file=__FILE__)) return

    ! add the nestedState to the state
    call ESMF_StateAdd(state, (/nestedState/), rc=rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=__LINE__, file=__FILE__)) return
    call ESMF_LogWrite("Add nest '"//trim(label)//"' to state.", &
      ESMF_LOGMSG_INFO, rc=rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=__LINE__, file=__FILE__)) return

    ! recursively populate the state
    call add_state_members(nestedState, config, trim(label)//":", &
      fieldListContainer, gridContainer, meshContainer, rc=rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=__LINE__, file=__FILE__)) return

  end subroutine add_nest

  !-----------------------------------------------------------------------------

  recursive subroutine add_fields(state, config, label, &
    fieldListContainer, gridContainer, meshContainer, rc)
    ! arguments
    type(ESMF_State), intent(inout) :: state
    type(ESMF_Config),intent(in)    :: config
    character(*),     intent(in)    :: label
    type(ESMF_Container)  :: fieldListContainer
    type(ESMF_Container)  :: gridContainer
    type(ESMF_Container)  :: meshContainer
    integer,          intent(out)   :: rc

    ! local variables
    type(ESMF_Config) :: configFields
    integer           :: count, i
    character(40)     :: tkS, geomS, fieldName
    character(ESMF_MAXSTR), pointer :: tokenList(:)
    type(ESMF_Grid)   :: grid
    type(ESMF_Mesh)   :: mesh
    type(ESMF_TypeKind_Flag) :: tk
    type(ESMF_Logical)  :: isPres
    type(FieldListWrap) :: flW

    rc = ESMF_SUCCESS

    ! check if the fieldList by this label already exists
    call c_ESMC_ContainerGetIsPresent(fieldListContainer, label, &
      isPres, rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=__LINE__, file=__FILE__)) return

    if (isPres == ESMF_TRUE) then
      ! query the fieldList from the container, and add it to the state
#if COMP_DEBUG_OUTPUT
      call ESMF_LogWrite("Query fieldList '"//trim(label)//"' from lookup.", &
        ESMF_LOGMSG_INFO, rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) return
#endif
      call ESMF_ContainerGetUDT(fieldListContainer, label, flW, rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) return
    else
      ! create a new fieldList and add to the state
#if COMP_DEBUG_OUTPUT
      call ESMF_LogWrite("Create fieldList '"//trim(label)//"' from scratch.", &
        ESMF_LOGMSG_INFO, rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) return
#endif
      allocate(flW%wrap)
      configFields = ESMF_ConfigCreate(config, &
        openlabel="<"//trim(label)//":", &
        closelabel=":"//trim(label)//">", &
        rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) return

      call ESMF_ConfigGetAttribute(configFields, label="count:", &
        value=count, rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) return
      call ESMF_ConfigGetAttribute(configFields, label="typekind:", &
        value=tkS, rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) return
      call ESMF_ConfigGetAttribute(configFields, label="geom:", &
        value=geomS, rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) return
      if (trim(tkS)=="I4") then
        tk = ESMF_TYPEKIND_I4
      else if (trim(tkS)=="I8") then
        tk = ESMF_TYPEKIND_I8
      else if (trim(tkS)=="R4") then
        tk = ESMF_TYPEKIND_R4
      else if (trim(tkS)=="R8") then
        tk = ESMF_TYPEKIND_R8
      else
        call ESMF_LogSetError(ESMF_RC_ARG_BAD, &
          msg="Specified typekind not supported", &
          line=__LINE__, file=__FILE__, rcToReturn=rc)
        return
      end if

      nullify(tokenList)
      call NUOPC_ChopString(trim(geomS), chopChar="-", &
        chopStringList=tokenList, rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) return
      if (size(tokenList) /= 2) then
        call ESMF_LogSetError(ESMF_RC_ARG_BAD, &
          msg="Format problem in geom string", &
          line=__LINE__, file=__FILE__, rcToReturn=rc)
        return
      end if
      if (tokenList(1) =="grid") then
        grid = create_grid(geomS, gridContainer, rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=__LINE__, file=__FILE__)) return
        allocate(flW%wrap%fieldList(count))
        do i=1, count
          write(fieldName,"(A,'-',I4.4)") trim(label), i
          flW%wrap%fieldList(i) = ESMF_FieldCreate(grid, typekind=tk, &
            name=fieldName, rc=rc)
          if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
            line=__LINE__, file=__FILE__)) return
        end do ! createflds(i)
      else if (tokenList(1) == "mesh") then
        mesh = create_mesh(geomS, meshContainer, rc=rc)
        if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
          line=__LINE__, file=__FILE__)) return
        allocate(flW%wrap%fieldList(count))
        do i=1, count
          write(fieldName,"(A,'-',I4.4)") trim(label), i
          flW%wrap%fieldList(i) = ESMF_FieldCreate(mesh, typekind=tk, &
            name=fieldName, rc=rc)
          if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
            line=__LINE__, file=__FILE__)) return
        end do ! createflds(i)
      else
        call ESMF_LogSetError(ESMF_RC_ARG_BAD, &
          msg="geom string is neither 'grid' nor 'mesh'", &
          line=__LINE__, file=__FILE__, rcToReturn=rc)
        return
      end if

      ! add the fieldList to the fieldList container for later lookup
      call ESMF_ContainerAddUDT(fieldListContainer, trim(label), flW, rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) return

      ! clean-up
      if (associated(tokenList)) deallocate(tokenList)
    end if

    ! add the fieldList to the state
    call ESMF_StateAdd(state, flW%wrap%fieldList, rc=rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=__LINE__, file=__FILE__)) return

  end subroutine add_fields

  !-----------------------------------------------------------------------------

  function create_grid(gridName, gridContainer, rc)
    type(ESMF_Grid)           :: create_grid
    character(*), intent(in)  :: gridName
    type(ESMF_Container)      :: gridContainer
    integer,      intent(out) :: rc

    type(ESMF_Logical)  :: isPres
    type(GridWrap)      :: gW

    rc = ESMF_SUCCESS

    ! check if the grid by this name already exists
    call c_ESMC_ContainerGetIsPresent(gridContainer, trim(gridName), &
      isPres, rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=__LINE__, file=__FILE__)) return

    if (isPres==ESMF_TRUE) then
      ! query the grid from the container
#if COMP_DEBUG_OUTPUT
      call ESMF_LogWrite("Query grid '"//trim(gridName)//"' from lookup.", &
        ESMF_LOGMSG_INFO, rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) return
#endif
      call ESMF_ContainerGetUDT(gridContainer, trim(gridName), gW, rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) return
    else
      ! must create a new fieldList and add to the state
#if COMP_DEBUG_OUTPUT
      call ESMF_LogWrite("Create grid '"//trim(gridName)//"' from scratch.", &
        ESMF_LOGMSG_INFO, rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) return
#endif
      allocate(gW%wrap)
      gW%wrap = ESMF_GridCreateNoPeriDimUfrm(maxIndex=(/100, 100/), &
        minCornerCoord=(/0._ESMF_KIND_R8,  -90._ESMF_KIND_R8/), &
        maxCornerCoord=(/360._ESMF_KIND_R8, 90._ESMF_KIND_R8/), &
        staggerLocList=(/ESMF_STAGGERLOC_CENTER, ESMF_STAGGERLOC_CORNER/), &
        name=gridName, rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) return

      ! add the grid to the grid container for later lookup
      call ESMF_ContainerAddUDT(gridContainer, trim(gridName), gW, rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) return
    end if

    create_grid = gW%wrap

  end function create_grid

  !-----------------------------------------------------------------------------

  function create_mesh(meshName, meshContainer, rc)
    type(ESMF_Mesh)           :: create_mesh
    type(ESMF_Container)      :: meshContainer
    character(*), intent(in)  :: meshName
    integer,      intent(out) :: rc

    type(ESMF_Logical)  :: isPres
    type(MeshWrap)      :: mW

    rc = ESMF_SUCCESS

    ! check if the mesh by this name already exists
    call c_ESMC_ContainerGetIsPresent(meshContainer, trim(meshName), &
      isPres, rc)
    if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
      line=__LINE__, file=__FILE__)) return

    if (isPres==ESMF_TRUE) then
       ! query the mesh from the container
#if COMP_DEBUG_OUTPUT
      call ESMF_LogWrite("Query mesh '"//trim(meshName)//"' from lookup.", &
        ESMF_LOGMSG_INFO, rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) return
#endif
      call ESMF_ContainerGetUDT(meshContainer, trim(meshName), mW, rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) return
    else
       ! must create a new fieldList and add to the state
#if COMP_DEBUG_OUTPUT
      call ESMF_LogWrite("Create mesh '"//trim(meshName)//"' from scratch.", &
        ESMF_LOGMSG_INFO, rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) return
#endif
      allocate(mW%wrap)
      mW%wrap = ESMF_MeshCreateCubedSphere(tileSize=50, &
        nx=10, ny=10, rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) return

      ! add the mesh to the mesh container for later lookup
      call ESMF_ContainerAddUDT(meshContainer, trim(meshName), mW, rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, &
        line=__LINE__, file=__FILE__)) return
    end if

    create_mesh = mW%wrap
  end function create_mesh

  !-----------------------------------------------------------------------------

end module comp
