#!/usr/bin/env python

from setuptools import find_packages, setup

# name can be any name.  This name will be used to create .egg file.
# name that is used in packages is the one that is used in the trac.ini file.
# use package name as entry_points
setup(
    name = 'TracAjaxComments',
    author = 'kostialopuhin',
    version = '0.1',
    url = 'http://trac-hacks.org/wiki/TracAjaxCommentsPlugin',
    description = 'AJAX style editing for ticket comments',
    zip_safe = True,
    packages = ['ajaxcomments'],
    package_data = {'ajaxcomments': ['templates/*.html','htdocs/js/*.js']},
    entry_points = {'trac.plugins': ['ajaxcomments = ajaxcomments']},
)
