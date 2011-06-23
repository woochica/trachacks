#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracNoAnonymous',
    version = '2.4',
    packages = ['noanonymous'],

    author = 'Pedro Paixao',
    author_email = 'pedro@readingtab.com',
    maintainer = 'Anatoly Techtonik',
    maintainer_email = 'techtonik@gmail.com',
    description = 'Redirect anonymous users to the login screen on PermissionError.',
    license = 'BSD',
    keywords = 'trac plugin',
    url = 'http://trac-hacks.org/wiki/NoAnonymousPlugin',
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['Trac'],

    entry_points = {
        'trac.plugins': [
            'noanonymous.filter = noanonymous.filter',
        ]
    },
)
