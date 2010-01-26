TEMPLATE = lib
TARGET = qxmlrpc
DESTDIR = ./
QT += network xml
CONFIG += staticlib
DEFINES += QT_LARGEFILE_SUPPORT QT_XML_LIB QT_NETWORK_LIB
INCLUDEPATH += . \
    ./.. \
    ./debug
PRECOMPILED_HEADER = stable.h
DEPENDPATH += .
MOC_DIR += debug
OBJECTS_DIR += debug
UI_DIR += GeneratedFiles
RCC_DIR += GeneratedFiles
include(qxmlrpc.pri)
