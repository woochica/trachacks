#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
 Copyright (C) 2008 General de Software de Canarias.
 
 Author: Claudio Manuel Fernández Barreiro <claudio.sphinx@gmail.com>
'''

from setuptools import setup

PACKAGE = 'TracWikiExport'
VERSION = '0.2'

setup(
    name = PACKAGE,
    version = VERSION,
    author = 'Claudio Manuel Fernández Barreiro, Carlos López Pérez',
    author_email = 'claudio.sphinx@gmail.com, carlos.lopezperez@gmail.com',
    description = "Plugin to export in different formats",
    long_description = "Plugin to export wiki pages in ODT, PDF and DOC formats",
    
    url = "http://trac-hacks.org/wiki/WikiExportPlugin",
    
    keywords = "trac odt pdf word plugin",
    
    packages = ['exportplugin'],
    entry_points = """
        [trac.plugins]
        TracWikiExportPlugin = exportplugin.export
    """,
    
    
)
