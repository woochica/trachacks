#!/bin/sh
VERSION=$TRAC
export PYTHONPATH=/opt/trac/$VERSION/lib/python2.7/site-packages/
export PATH=$PATH:/opt/trac/$VERSION/bin/
export ENV=/home/roman/Trac
trac-admin $1
