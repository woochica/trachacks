#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from tracextlinksnewwindow.plugin import __revision__ as coderev

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int(r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]

rev = str( max( coderev, __revision__ ) )

setup(
    name = 'TracExtLinksNewWindow',
    version = '0.2.' + rev,
    description = 'Trac Load External Links in New Window',
    license = 'GPLv3',
    url = 'http://trac-hacks.org/wiki/ExternalLinksNewWindow',
    author = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    packages = ['tracextlinksnewwindow'],
    package_data = {
        'tracextlinksnewwindow' : [ 'htdocs/*.js' ],
    },
    entry_points = {
        'trac.plugins': [
            'tracextlinksnewwindow.plugin = tracextlinksnewwindow.plugin',
        ],
    }
)
