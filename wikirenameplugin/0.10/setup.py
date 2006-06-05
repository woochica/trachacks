#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'WikiRename',
    version = '0.01',
    packages = ['wikirename'],
    package_data={
        'wikirename' : [ 'templates/*.cs' ],
    },

    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "Add simple support for renaming/moving wiki pages",
    license = "BSD",
    keywords = "wiki page rename",
    url = "http://trac-hacks.org",

    entry_points = {
        'trac.plugins': [
            'wikirename.web_ui = wikirename.web_ui',
        ],
        'console_scripts': [
            'trac-wikirename = wikirename.script:run'
        ],
    },
    
    install_requires = [ 'TracWebAdmin', 'CtxtnavAdd' ],
)
