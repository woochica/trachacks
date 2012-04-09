#! /bin/sh

ENV=/Users/peter/projects/env0.10
PORT=9010

export PATH=$ENV/bin:$PATHRESET

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
