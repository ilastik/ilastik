cmake_minimum_required(VERSION 2.8)
PROJECT(drtile)

find_package(Vigranumpy REQUIRED PATHS ${Vigranumpy_DIR})
SET(Vigranumpy_DIR ${Vigranumpy_DIR}
    CACHE PATH "Directory containing VigranumpyConfig.cmake"
    FORCE)
message(STATUS "Vigranumpy found at: ${Vigranumpy_CONFIG}")

add_vigranumpy_module(drtile SOURCES drtile.cpp)
