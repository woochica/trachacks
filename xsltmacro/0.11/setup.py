#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

PACKAGE = 'xslt'
VERSION = '0.8'

setup(
    name=PACKAGE,
    version=VERSION,
    packages=['xslt'],

    author = "Ronald Tschalär",
    description = "Macro to display the results of an XSL-tranforms in a page",
    license = "BSD",
    keywords = "trac wiki xslt macro",
    url = "http://trac-hacks.org/wiki/XsltMacro",

    entry_points = {
        'trac.plugins': [
            'xslt = xslt.Xslt'
        ]
    }
)
