cmake_minimum_required(VERSION 3.16)

project(demo_app VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(FetchContent)

FetchContent_Declare(
    portable_file_dialogs
    URL https://github.com/samhocevar/portable-file-dialogs/archive/refs/tags/0.1.0.tar.gz
    DOWNLOAD_EXTRACT_TIMESTAMP TRUE
)

FetchContent_GetProperties(portable_file_dialogs)
if(NOT portable_file_dialogs_POPULATED)
    if(POLICY CMP0169)
        cmake_policy(SET CMP0169 OLD)
    endif()
    FetchContent_Populate(portable_file_dialogs)
endif()

if(NOT TARGET portable_file_dialogs)
    add_library(portable_file_dialogs INTERFACE)
    target_include_directories(portable_file_dialogs INTERFACE ${portable_file_dialogs_SOURCE_DIR})
endif()

add_executable(demo_easyinstaller
    main.cpp
)

target_include_directories(demo_easyinstaller PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(demo_easyinstaller PRIVATE portable_file_dialogs)

if(APPLE)
    set_target_properties(demo_easyinstaller PROPERTIES
        BUILD_RPATH "@loader_path"
        INSTALL_RPATH "@loader_path"
    )
elseif(UNIX)
    set_target_properties(demo_easyinstaller PROPERTIES
        BUILD_RPATH "$ORIGIN"
        INSTALL_RPATH "$ORIGIN"
    )
endif()

install(TARGETS demo_easyinstaller
    RUNTIME DESTINATION .
)
