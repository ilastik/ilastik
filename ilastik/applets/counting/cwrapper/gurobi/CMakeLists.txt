include_directories(${Gurobi_INCLUDE_DIR})
add_library(gurobiwrapper SHARED gurobiwrapper)
target_link_libraries(gurobiwrapper ${Gurobi_LIBRARY})
INSTALL(TARGETS gurobiwrapper
  LIBRARY DESTINATION lib
  ARCHIVE DESTINATION lib
  )
