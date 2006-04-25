#! /bin/sh -x

rm -rf build
rm -rf dist
python setup.py bdist_egg
rm -f env/trac/plugins/TracPageList-*.egg
cp dist/TracPageList-*.egg env/trac/plugins/

#sudo /etc/init.d/apache2 restart

tracd --port 8080 env/trac/
