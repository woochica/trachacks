

TEMPLATE = app
TARGET = trac2xml
DESTDIR = ../Debug
QT += network xml xmlpatterns
CONFIG += debug
DEFINES += QT_XML_LIB QT_NETWORK_LIB
INCLUDEPATH += ./GeneratedFiles \
    ./GeneratedFiles/Debug \
    ./.. \
    .

debug{    
LIBS+= -L"./../xmlrpc" \
	-lqxmlrpc_debug 
}
DEPENDPATH += .
MOC_DIR += ./GeneratedFiles/debug
OBJECTS_DIR += debug
UI_DIR += ./GeneratedFiles
RCC_DIR += ./GeneratedFiles
include(trac2project.pri)
