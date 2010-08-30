#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + ur"$Rev$"[6:-2])
__date__     = ur"$Date$"[7:-2]

setup(
    name         = 'TracExtLinksNewWindow',
    version      = '1.0',
    description  = 'Trac Load External Links in New Window',
    license      = 'GPLv3',
    zip_safe     = False,
    url          = 'http://trac-hacks.org/wiki/ExternalLinksNewWindow',
    download_url = 'http://trac-hacks.org/svn/externallinksnewwindowplugin/releases',
    author       = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    packages     = ['tracextlinksnewwindow'],
    package_data = {
        'tracextlinksnewwindow' : [ 'htdocs/*.js' ],
    },
    entry_points = {
        'trac.plugins': [
            'tracextlinksnewwindow.plugin = tracextlinksnewwindow.plugin',
        ],
    }
)
