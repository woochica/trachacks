#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracNavControl',
    version = '1.0',
    packages = ['navcontrol'],

    author = "BRODO",
    author_email = "tsooboi@gmail.com",
    description = "Manipulate the Trac navigation bars. Hiding, moving and renaming items",
    license = "BSD",
    keywords = "trac plugin navigation menu remove hide rename move",
    url = "http://trac-hacks.org/wiki/NavControlPlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    

    entry_points = {
        'trac.plugins': [
            'navcontrol.filter = navcontrol.filter',
        ]
    }
)
