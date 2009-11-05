#!/usr/bin/env python

from setuptools import setup
from tracmindmap.macro import __revision__ as coderev

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]

rev = str( max( coderev, __revision__ ) )

setup(
    name = 'TracMindMapMacro',
    version = '0.2.' + rev,
    packages = ['tracmindmap'],
    package_data = {
        'tracmindmap' : [ 'htdocs/*.swf', 'htdocs/*.js' ],
    },
    author = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description = "Trac Macro to display Freemind mindmaps using a Flash app.",
    url = 'http://www.trac-hacks.org/wiki/MindMapMacro',
    license      = 'GPLv3',
    zip_safe     = False,
    keywords = 'trac mindmap freemind flash macro',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': [
      'tracmindmap.macro = tracmindmap.macro',
     ]}
)
