cmake_minimum_required(VERSION 3.10)
project(peristaltic-pumps)

# Add the include directory
include_directories(${CMAKE_SOURCE_DIR}/lib/EepromManager)

# Add a dummy executable to help CLion index the files
add_executable(dummy_executable src/main.cpp)