cmake_minimum_required(VERSION 3.15)
project(ghostdav_core_engine)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(OpenSSL REQUIRED)

# Include directories
include_directories(${OPENSSL_INCLUDE_DIR})
include_directories(crypto)
include_directories(stego)
include_directories(media)

# Source files
set(SOURCES
    main.cpp
    crypto/encrypt.cpp
    crypto/decrypt.cpp
    stego/embed.cpp
    stego/extract.cpp
    stego/image_utils.cpp
    media/encoder.cpp
    media/decoder.cpp
    media/stream.cpp
)

# Create library
add_library(ghostdav_core SHARED ${SOURCES})

# Link libraries
target_link_libraries(ghostdav_core PRIVATE ${OPENSSL_LIBRARIES})

# Optional: Create Python bindings with PyO3/pyo3
# This would require Rust with PyO3 for proper Python integration
# Or use SWIG for C++ to Python binding

# Install
install(TARGETS ghostdav_core
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin)
