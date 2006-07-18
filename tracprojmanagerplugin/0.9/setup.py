#!/usr/bin/env python

from setuptools import setup, find_packages

PACKAGE = 'Trac Project Manager'
VERSION = '0.1'

setup(
    name=PACKAGE,
    version=VERSION,
    author = 'Ricardo Salveti',
    author_email = 'rsalveti@gmail.com',
    url = 'http://www.trac-hacks.org/wiki/TracProjManagerPlugin',
    description = 'A Project Manager profile with permission to edit project details, versions and components',
    license='BSD',
    packages=find_packages(exclude=['ez_setup', '*.tests*']),
    package_data={
                'projmanager': [
                'htdocs/css/*.css',
                'templates/*.cs'
                ]
    },
    entry_points = {
                'trac.plugins': [
                'projmanager.web_ui = projmanager.web_ui',
                'projmanager.basics = projmanager.basics',
                'projmanager.version = projmanager.version',
                'projmanager.component = projmanager.component'
                ]
    }      
)
