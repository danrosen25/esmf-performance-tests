#!/bin/bash

find_system () {
  local sysname=`hostname`
  sysname="${sysname//[[:digit:]]/}"
  echo ${sysname}
}

setup_system () {
  local sysname=$1
  local modfdir=$2
  case ${sysname} in
    "derecho")
      module use ${modfdir}
      module load ${sysname}
      BATCHSYS="${BATCHSYS:-qsub}"
      CPERNODE="${CPERNODE:-64}" ;;
    *) printf "\e[91mERROR: no modulefile file for ${sysname}"
       printf " in ${modfdir}\e[0m\n"
       exit 1 ;;
  esac
}
