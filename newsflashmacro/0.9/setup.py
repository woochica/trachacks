#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracNewsFlash',
    version = '0.1',
    packages = ['newsflash'],
    package_data={ 'newsflash' : [ 'htdocs/css/*.css' ] },
    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "Make a colored box.",
    license = "BSD",
    keywords = "trac plugin macro news flash",
    url = "http://trac-hacks.org/wiki/NewsFlashMacro",

    entry_points = {
        'trac.plugins': [
            'newsflash.macro = newsflash.macro',
        ],
    },

)
