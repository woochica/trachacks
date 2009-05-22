#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'BambooTrac',
    version = '0.1',
    author = "grimsy",
    description = "A trac plugin to add bamboo build info to the trac timeline",
    license = "BSD",
    keywords = "trac builds bamboo",
    url = "http://trac-hacks.org/wiki/BambooTracPlugin",

    packages = ['BambooTrac'],
    package_data = {
        'BambooTrac' : ['htdocs/*.css', 'htdocs/*.gif']
    },
    entry_points = {
        'trac.plugins' : [ 'BambooTrac = BambooTrac.BambooTracPlugin' ]
    }
)
