#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Setup file for the
= Watchlist Plugin for Trac =
Plugin Website:  http://trac-hacks.org/wiki/WatchlistPlugin
Trac website:    http://trac.edgewall.org/

Copyright (c) 2008-2010 by Martin Scharrer <martin@scharrer-online.de>
All rights reserved.

The i18n support was added by Steffen Hoffmann <hoff.st@web.de>.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For a copy of the GNU General Public License see
<http://www.gnu.org/licenses/>.

$Id$
"""

from setuptools import setup

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + ur"$Rev$"[6:-2])
__date__     = ur"$Date$"[7:-2]


extra = {}

try:
    from trac.util.dist  import  get_l10n_cmdclass
    cmdclass = get_l10n_cmdclass()
    if cmdclass:
        extra['cmdclass'] = cmdclass
        extractors = [
            ('*.py',              'python', None),
            ('templates/**.html', 'genshi', None),
        ]
        extra['message_extractors'] = {
            'tracwatchlist': extractors,
        }
except ImportError:
    pass

setup(
    name = 'TracWatchlistPlugin',
    version = '1.0',
    description = "Watchlist Plugin for Trac 0.11/0.12",
    keywords = 'trac watchlist wiki plugin',
    author = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    url = 'http://www.trac-hacks.org/wiki/WatchlistPlugin',
    download_url = 'http://trac-hacks.org/svn/watchlistplugin/releases/',
    license      = 'GPLv3',
    classifiers = ['Framework :: Trac'],
    #install_requires = ['Babel>= 0.9.5', 'Trac >= 0.11'],
    install_requires = ['Trac >= 0.11'],
    packages = ['tracwatchlist'],
    package_data = {
        'tracwatchlist' : [
            'render/*.py',
            'templates/*.html',
            'htdocs/ico/*',
            'htdocs/css/*.css',
            'htdocs/js/*.js',
            'locale/*/LC_MESSAGES/*.mo',
            'manuals/*.txt',
            'manuals/attachments/*/*',
        ],
    },
    zip_safe     = False,
    entry_points = {'trac.plugins':
      [
        'tracwatchlist = tracwatchlist',
        'tracwatchlist.plugin = tracwatchlist.plugin',
        'tracwatchlist.ticket = tracwatchlist.ticket',
        'tracwatchlist.wiki = tracwatchlist.wiki',
        'tracwatchlist.util = tracwatchlist.util',
        'tracwatchlist.db = tracwatchlist.db',
        'tracwatchlist.nav = tracwatchlist.nav',
        'tracwatchlist.render = tracwatchlist.render',
        'tracwatchlist.translation = tracwatchlist.translation',
        'tracwatchlist.manual = tracwatchlist.manual',
      ]},
    **extra
)
