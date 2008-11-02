#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'TracShortcutIconPlugin',
    version = '0.1',
    packages = ['tracshortcuticon'],
    author = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description = "Configurables shortcut icons for Trac.",
    url = 'http://www.trac-hacks.org/wiki/ShortcutIconPlugin',
    license = 'GPLv3',
    keywords = 'trac plugin favicon shortcuticon',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['tracshortcuticon.plugin = tracshortcuticon.plugin']}
)
