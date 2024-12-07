cmake_minimum_required(VERSION 3.16)
project(add_schema VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets)

if(WIN32)
    add_executable(add_schema WIN32
        main.cpp
        mainwindow.cpp
        mainwindow.h
    )
else()
    add_executable(add_schema
        main.cpp
        mainwindow.cpp
        mainwindow.h
    )
endif()

target_link_libraries(add_schema PRIVATE
    Qt6::Core
    Qt6::Gui
    Qt6::Widgets
)

if(WIN32)
    message("Packaging for Windows")
elseif(APPLE)
    message("Packaging for macOS")
    set_target_properties(add_schema PROPERTIES
        MACOSX_BUNDLE TRUE
    )
endif()
