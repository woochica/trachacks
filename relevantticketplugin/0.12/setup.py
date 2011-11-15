# -*- coding: utf-8 -*-
from setuptools import setup

setup(
    name = 'relevantticket',
    version = '0.1',
    packages = ['relevantticketplugin'],
    description = 'relevantticketplugin',
    author = 'ONE',
    url = 'http://www.clstyle.net/',
    entry_points = {'trac.plugins': ['relevantticketplugin = relevantticketplugin']},
    license = 'New BSD')
    