VERSION_11=0.7c
VERSION_10=0.6c

build_project_egg() {
    echo Building the egg for $PROJECT on $PYTHON...
    pushd $PROJECT
    rm -rf *.egg-info build
    rm -rf dist/*
    $PYTHON -E setup.py bdist_egg
    popd
}


mkdir build

PROJECT=0.11
PYTHON=/sw/bin/python2.4
build_project_egg
cp $PROJECT/dist/TicketImport-$VERSION_11-py2.4.egg build/

PYTHON=/sw/bin/python2.5
build_project_egg
cp $PROJECT/dist/TicketImport-$VERSION_11-py2.5.egg build/

PROJECT=0.10

PYTHON=/sw/bin/python2.4
build_project_egg
cp $PROJECT/dist/TicketImport-$VERSION_10-py2.4.egg build/

PYTHON=/sw/bin/python2.5
build_project_egg
cp $PROJECT/dist/TicketImport-$VERSION_10-py2.5.egg build/
