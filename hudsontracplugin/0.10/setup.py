#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'HudsonTrac',
    version = '0.5',
    author = "Ronald Tschalär",
    description = "A trac plugin to add hudson build info to the trac timeline",
    license = "BSD",
    keywords = "trac builds hudson",
    url = "http://trac-hacks.org/wiki/HudsonTracPlugin",

    packages = ['HudsonTrac'],
    package_data = {
        'HudsonTrac' : ['htdocs/*.css', 'htdocs/*.gif']
    },
    entry_points = {
        'trac.plugins' : [ 'HudsonTrac = HudsonTrac.HudsonTracPlugin' ]
    }
)
