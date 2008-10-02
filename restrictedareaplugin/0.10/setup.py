#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracRestrictedArea',
    version = '1.0.1',
    packages = ['restrictedarea'],

    author = "Christian Spurk, DFKI GmbH",
    author_email = "Christian.Spurk@dfki.de",
    description = "Allows the setup of restricted areas with access only for privileged users.",
    license = "revised BSD license",
    keywords = "trac plugin restricted area access",
    url = "http://trac-hacks.org/wiki/RestrictedAreaPlugin",
    classifiers = [
        'Framework :: Trac',
    ],

    entry_points = {
        'trac.plugins': [
            'restrictedarea.filter = restrictedarea.filter',
        ]
    }
)
