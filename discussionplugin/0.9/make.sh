python setup.py bdist_egg
cp dist/*.egg /var/lib/trac/Test/plugins
tracd -p 8000 --auth *,/var/lib/trac/Test/conf/htdigest,damien /var/lib/trac/Test/
