#!/bin/bash

# This file really isn't meant for anyone else other than Tim Coulter.
# Remove as neccessary.

TRAC_ENV="/home/tcoulter/workspace/trac"

echo $TRAC_ENV

cd ./0.11/
python setup.py bdist_egg
cp dist/*.egg $TRAC_ENV/plugins/
trac-admin $TRAC_ENV upgrade
tracd --port 8000 --auth=trac,../passwords.txt,trac $TRAC_ENV
