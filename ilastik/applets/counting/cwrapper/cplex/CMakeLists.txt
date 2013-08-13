include_directories(${CPLEX_INCLUDE_DIR} ${CONCERT_INCLUDE_DIR})
link_directories(${CPLEX_LIBRARY_DIR})
set(CMAKE_CXX_FLAGS ${CMAKE_CXX_FLAGS} -DIL_STD)
add_library(cplexwrapper SHARED cplexwrapper)
#add_library(cplexwrapper2 SHARED cplex)
#target_link_libraries(cplexwrapper2 ${ILOCPLEX_LIBRARY} ${CPLEX_LIBRARY} ${CONCERT_LIBRARY})
target_link_libraries(cplexwrapper ${CPLEX_LIBRARY})
INSTALL(TARGETS cplexwrapper
  LIBRARY DESTINATION lib)
