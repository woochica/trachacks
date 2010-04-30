#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

PACKAGE = 'macrochain'
VERSION = '0.2'

setup(
    name=PACKAGE,
    version=VERSION,
    packages=['macrochain'],

    author = "Ronald Tschalär",
    description = "Macro to chain multiple macros together",
    license = "BSD",
    keywords = "trac wiki chain macro",
    url = "http://trac-hacks.org/wiki/MacroChain",

    entry_points = {
        'trac.plugins': [
            'macrochain = macrochain.MacroChain'
        ]
    }
)
