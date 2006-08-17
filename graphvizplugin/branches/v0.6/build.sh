#! /bin/sh

if [ "x$1" == "x" ]; then
    echo "build.sh env0.9|env0.10"
    exit 1
fi

ENV=/home/peter/projects/$1
export PATH=$ENV/bin:$PATHRESET

echo "cleaning out old build"
rm -rf build dist
python setup.py bdist_egg

echo "cleaning out old installation"
rm -f $ENV/trac/plugins/graphviz-*.egg
rm -f $ENV/trac/htdocs/graphviz/*

echo "running tracd"
cp dist/graphviz-*.egg $ENV/trac/plugins/
LD_LIBRARY_PATH=$ENV/lib tracd --port 9009 $ENV/trac
