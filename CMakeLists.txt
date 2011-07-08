cmake_minimum_required(VERSION 2.8)
PROJECT(context)
set(CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR})
find_package(Vigra REQUIRED)
find_package(Boost COMPONENTS python REQUIRED)
find_package(PythonLibs REQUIRED)
find_package(Numpy REQUIRED)

include_directories(
    ${VIGRA_INCLUDE_DIR}
    ${PYTHON_NUMPY_INCLUDE_DIR}
    ${Boost_INCLUDE_DIR}
    ${PYTHON_INCLUDE_DIRS}
    ${PYTHON_INCLUDE_PATH}
)
add_library(context SHARED pythonContextMulti.cxx)
message("xxx ${Boost_PYTHON_LIBRARY} ${VIGRA_NUMPY_CORE_LIBRARY} ${VIGRA_NUMPY_IMPEX_LIBRARY}")
target_link_libraries(context ${Boost_PYTHON_LIBRARY} ${VIGRA_NUMPY_CORE_LIBRARY} ${PYTHON_LIBRARY})
IF(WIN32)
    SET_TARGET_PROPERTIES(context PROPERTIES OUTPUT_NAME "context" PREFIX "" SUFFIX  ".pyd")
ELSEIF(MACOSX)
    SET_TARGET_PROPERTIES(context PROPERTIES OUTPUT_NAME "context" PREFIX "" SUFFIX ".so")
ELSE()
    SET_TARGET_PROPERTIES(context PROPERTIES OUTPUT_NAME "context" PREFIX "")
ENDIF()

