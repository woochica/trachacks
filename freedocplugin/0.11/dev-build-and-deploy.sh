#!/bin/sh
#
# License: BSDLike
# Rick van der Zwet <info@rickvanderzwet.nl>

TARGET=${1:-/usr/local/www/trac/tracs/personal/plugins/}
WEBSERVER_USER=${2:-www}

rm dist/*
python setup.py bdist_egg
sudo rm -v $TARGET/TracFreeDoc*
sudo -u www cp dist/* $TARGET 

