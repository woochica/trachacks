#! /bin/sh

case "$1" in
  9)
    ENV=/home/peter/projects/env0.9
    PORT=9009
    ;;
  10)
    ENV=/home/peter/projects/env0.10
    PORT=9010
    ;;
  *)
    echo "build.sh 9|10"
    exit 1
esac


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
