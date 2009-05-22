#!/bin/sh

coverage -e
rm -f codeexample/tests/*.pyc
rm -f codeexample/*.pyc
coverage -x setup.py test
coverage -rm -o /usr codeexample/tests/*.py codeexample/*.py