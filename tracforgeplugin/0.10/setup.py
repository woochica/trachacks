#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracForge',
    version = '1.0',
    packages = ['tracforge'],
    package_data={ 'tracforge' : [ 'templates/*.cs' ] },
    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "Experimental multi-project support.",
    long_description = "A suite of plugins to link a set of related projects.",
    license = "BSD",
    keywords = "trac plugin forge multi project",
    url = "http://trac-hacks.org/wiki/TracForgePlugin",

    entry_points = {
        'trac.plugins': [
            #'tracforge.web_ui = tracforge.web_ui',
        ],
    },

    install_requires = [ 'TracWebAdmin' ],
)
