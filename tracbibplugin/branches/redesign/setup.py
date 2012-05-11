#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'TracBib',
    version = 'Snapshot',
    packages = ['tracbib'],
    author = 'Roman Fenkhuber',
    author_email = 'roman@fenkhuber.at',
    description = "Macro to allow the usage of bibtex files in the versioncontrol system to cite ressources in the wiki pages",
    url = 'http://www.trac-hacks.org/wiki/TracBib',
    license = 'gpl',
    keywords = 'trac plugin cite macro bibtex',
    classifiers = ['Framework :: Trac'],
    package_data={'tracbib' : ['htdocs/*.css','htdocs/*.js']},
    entry_points = {'trac.plugins': ['tracbib.tracib=tracbib.tracbib','tracbib.source=tracbib.source','tracbib.ieeelike=tracbib.ieeelike']}
)
