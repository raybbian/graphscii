cmake_minimum_required(VERSION 3.26)
project(graphscii)

set(CMAKE_CXX_STANDARD 20)

add_executable(graphscii main.cpp)


# tests
#[[
find_package(Catch2 REQUIRED)
add_executable(tests )
target_link_libraries(tests PRIVATE Catch2::Catch2WithMain)

include(CTest)
include(Catch)
catch_discover_tests(tests)
]]
