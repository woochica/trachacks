#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracRewrite',
    version = '0.1',
    packages = ['tracrewrite'],
    #package_data={
    #    'tracrewrite' : ['templates/*.css' ],
    #},

    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "Trac version of mod_rewrite",
    license = "BSD",
    keywords = "trac plugin mod_rewrite",
    url = "https://xil.arc.rpi.edu",

    entry_points = {
        'trac.plugins': [
            'tracrewrite.web_ui = tracrewrite.web_ui',
        ],
    }
)
