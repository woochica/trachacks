# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

# name can be any name.  This name will be used to create .egg file.
# name that is used in packages is the one that is used in the trac.ini file.
# use package name as entry_points
setup(
    name='Planetforge/Trac import/export Plugin', version='0.2',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = {
        'trac.plugins': [
            'planetforgeimportexport = planetforgeimportexport' ]},
    package_data={'planetforgeimportexport': ['templates/*.html']},

    author = u'Bearstech',
    author_email = 'vcaron@bearstech.com',
    description = 'Export/import all Trac items in "PlanetForge" format',
    license = 'GPL 3.0',
    url = "http://bearstech.com"
)
