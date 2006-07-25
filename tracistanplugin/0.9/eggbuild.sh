#!/bin/bash

if [ -z ${1} ]; then
  echo "You must specify a setup.py file"
  exit 1
fi
rm -rf build
rm -rf dist
rm -rf *.egg-info
python ${1} bdist_egg
