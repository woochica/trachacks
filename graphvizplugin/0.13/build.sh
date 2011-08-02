#! /bin/sh

echo $PATH

ENV=/opt/trac/py25/env0.11
PORT=9011

export PATH=$ENV/bin:$PATH_RESET

echo "cleaning out old build"
rm -rf build dist
python setup.py bdist_egg

echo "cleaning out old installation"
rm -f $ENV/trac/plugins/graphviz-*.egg
rm -f $ENV/trac/htdocs/graphviz/*

echo "running tracd on port $PORT"
cp dist/graphviz-*.egg $ENV/trac/plugins/
#LD_LIBRARY_PATH=$ENV/lib tracd --port $PORT -b 172.16.6.1 $ENV/trac
LD_LIBRARY_PATH=$ENV/lib tracd --port $PORT $ENV/trac
