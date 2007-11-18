#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracAddCommentMacro',
    version = '0.3',
    packages = ['addcomment'],
    package_data={ 'addcomment' : [  ] },
    author = "Alec Thomas",
    description = "Macro to add comments to a wiki page.",
    license = "BSD",
    keywords = "trac plugin macro comments",
    url = "http://trac-hacks.org/wiki/AddCommentMacro",
    classifiers = [
        'Framework :: Trac',
    ],
    
    entry_points = {
        'trac.plugins': [
            'addcomment.macro = addcomment.macro',
        ],
    },

    install_requires = [ 'TracMacroPost>=0.2' ],
)
