# This module finds cplex.
#
# User can give CPLEX_ROOT_DIR as a hint stored in the cmake cache.
#
# It sets the following variables:
#  CPLEX_FOUND              - Set to false, or undefined, if cplex isn't found.
#  CPLEX_INCLUDE_DIRS       - include directory
#  CPLEX_LIBRARIES          - library files

## config
set(CPLEX_ROOT_DIR "$ENV{CPLEX_ROOT_DIR}" CACHE PATH "CPLEX root directory")

if(WIN32)
execute_process(COMMAND where cplex
	OUTPUT_VARIABLE CPLEX_BIN_PATH OUTPUT_STRIP_TRAILING_WHITESPACE)
FILE(TO_CMAKE_PATH ${CPLEX_BIN_PATH} CPLEX_BIN_PATH)
SET(CPLEX_HINT_DIR "${CPLEX_BIN_PATH}/../../../" CACHE PATH "Cplex root directory2")
endif(WIN32)


FIND_PATH(CPLEX_INCLUDE_DIR
  ilcplex/cplex.h
  HINTS ${CPLEX_ROOT_DIR}/cplex/include
        ${CPLEX_ROOT_DIR}/include
  ${CPLEX_HINT_DIR}/include
  PATHS ENV C_INCLUDE_PATH
        ENV C_PLUS_INCLUDE_PATH
        ENV INCLUDE_PATH
  )

IF(CPLEX_INCLUDE_DIR)
TRY_RUN(
  RUN_RESULT_VAR COMPILE_RESULT_VAR
  ${CMAKE_BINARY_DIR} 
  ${CMAKE_CURRENT_SOURCE_DIR}/findcplexversion.c
  CMAKE_FLAGS
  -DINCLUDE_DIRECTORIES:STRING=${CPLEX_INCLUDE_DIR}
  RUN_OUTPUT_VARIABLE CPLEX_WIN_VERSION
  )
SET (CPLEX_WIN_VERSION ${CPLEX_WIN_VERSION} CACHE STRING "Cplex version integer code. Necessary on Windows to determine the library name")
ENDIF(CPLEX_INCLUDE_DIR)
MESSAGE("-- Found Cplex Version = ${CPLEX_WIN_VERSION}")
if(WIN32)
  if(NOT CPLEX_WIN_VS_VERSION)
    set(CPLEX_WIN_VS_VERSION 2010 CACHE STRING "Cplex Visual Studio version, for instance 2008 or 2010.")
  endif(NOT CPLEX_WIN_VS_VERSION)

  if(NOT CPLEX_WIN_LINKAGE)
    set(CPLEX_WIN_LINKAGE mda CACHE STRING "Cplex linkage variant on Windows. One of these: mda (dll, release), mdd (dll, debug), mta (static, release), mtd (static, debug)")
  endif(NOT CPLEX_WIN_LINKAGE)

  if(NOT CPLEX_WIN_BITNESS)
    set(CPLEX_WIN_BITNESS x64 CACHE STRING "On Windows: x86 or x64 (32bit resp. 64bit)")
  endif(NOT CPLEX_WIN_BITNESS)

  # now, generate platform string
  set(CPLEX_WIN_PLATFORM "${CPLEX_WIN_BITNESS}_windows_vs${CPLEX_WIN_VS_VERSION}/stat_${CPLEX_WIN_LINKAGE}")

else(WIN32)
  set(CPLEX_WIN_PLATFORM "")
endif(WIN32)

## cplex root dir guessing
# windows: trying to guess the root dir from a 
# env variable set by the cplex installer
FIND_LIBRARY(CPLEX_LIBRARY
  NAMES cplex cplex${CPLEX_WIN_VERSION}
  HINTS ${CPLEX_ROOT_DIR}/cplex/lib/${CPLEX_WIN_PLATFORM} #windows
        ${WIN_ROOT_GUESS}/cplex/lib/${CPLEX_WIN_PLATFORM} #windows
  	${CPLEX_HINT_DIR}/lib/${CPLEX_WIN_PLATFORM} #windows
        ${CPLEX_ROOT_DIR}/cplex/lib/x86-64_debian4.0_4.1/static_pic #unix
        ${CPLEX_ROOT_DIR}/cplex/lib/x86-64_sles10_4.1/static_pic #unix 
  PATHS ENV LIBRARY_PATH #unix
        ENV LD_LIBRARY_PATH #unix
  )
message(STATUS "CPLEX Library: ${CPLEX_LIBRARY}")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(CPLEX DEFAULT_MSG 
 CPLEX_LIBRARY CPLEX_INCLUDE_DIR )


IF(CPLEX_FOUND)
  SET(CPLEX_INCLUDE_DIRS ${CPLEX_INCLUDE_DIR} )
  SET(CPLEX_LIBRARIES ${CPLEX_LIBRARY} )
  IF(CMAKE_SYSTEM_NAME STREQUAL "Linux")
    SET(CPLEX_LIBRARIES "${CPLEX_LIBRARIES};m;pthread")
  ENDIF(CMAKE_SYSTEM_NAME STREQUAL "Linux")
ENDIF(CPLEX_FOUND)

MARK_AS_ADVANCED(CPLEX_LIBRARY CPLEX_INCLUDE_DIR )
