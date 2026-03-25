cmake_minimum_required(VERSION 3.16)

project(easyinstaller_example VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(easyinstaller_name SHARED
    easyinstaller_name.cpp
)

target_include_directories(easyinstaller_name PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_definitions(easyinstaller_name PRIVATE EASYINSTALLER_NAME_EXPORTS)

add_executable(demo_easyinstaller
    main.cpp
)

target_link_libraries(demo_easyinstaller PRIVATE easyinstaller_name)

if(APPLE)
    set_target_properties(demo_easyinstaller PROPERTIES
        BUILD_RPATH "@loader_path"
        INSTALL_RPATH "@loader_path"
    )
    set_target_properties(easyinstaller_name PROPERTIES
        MACOSX_RPATH ON
    )
elseif(UNIX)
    set_target_properties(demo_easyinstaller PROPERTIES
        BUILD_RPATH "$ORIGIN"
        INSTALL_RPATH "$ORIGIN"
    )
endif()

install(TARGETS demo_easyinstaller easyinstaller_name
    RUNTIME DESTINATION .
    LIBRARY DESTINATION .
    ARCHIVE DESTINATION .
)
