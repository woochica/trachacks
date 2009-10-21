# -*- coding: utf-8 -*-
from setuptools import find_packages, setup

# name can be any name.  This name will be used to create .egg file.
# name that is used in packages is the one that is used in the trac.ini file.
# use package name as entry_points

setup(
    name='TracHtGroupEditorPlugin',
    version='2.0',
    author = 'Robert Martin',
    author_email = 'robert.martin@arqiva.com',
    description = 'HT Group Editor plugin for Trac',
    url = 'http://trac-hacks.org/wiki/TracGroupsEditor',
    license = 'GPL',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = {
        'trac.plugins' : ['HtGroupEditor = htgroupeditor']
    },
    package_data={'HtGroupEditor':['templates/*.html',
                                'htdocs/css/*.css']},
    install_requires = ['Trac >=0.11', 'configobj'],
)

