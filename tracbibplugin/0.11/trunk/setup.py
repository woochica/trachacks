#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'TracBib',
    version = 'Snapshot',
    packages = ['tracbib'],
    author = 'Roman Fenkhuber',
    author_email = 'a0401241@unet.univie.ac.at',
    description = "Macro to allow the usage of bibtex files in the versioncontrol system to cite ressources in the wiki pages",
    url = 'http://www.trac-hacks.org/wiki/TracBib',
    license = 'gpl',
    keywords = 'trac plugin cite macro bibtex',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['tracbib.macro = tracbib.tracbib']}
)
