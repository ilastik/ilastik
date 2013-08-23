include_directories(${CPLEX_INCLUDE_DIR})
link_directories(${CPLEX_LIBRARY_DIR})
add_library(cplexwrapper SHARED cplexwrapper)
target_link_libraries(cplexwrapper ${CPLEX_LIBRARY})
INSTALL(TARGETS cplexwrapper
  LIBRARY DESTINATION lib
  ARCHIVE DESTINATION lib
  )
