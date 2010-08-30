#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + ur"$Rev$"[6:-2])
__date__     = ur"$Date$"[7:-2]

setup(
    name = 'TracWatchlistPlugin',
    version = '0.5',
    packages = ['tracwatchlist'],
    author = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    package_data = {
        'tracwatchlist' : [
            'htdocs/ico/*',
            'htdocs/css/style.css',
            'htdocs/css/tablesorter.css',
            'htdocs/js/jquery.tablesorter.min.js',
            'htdocs/js/jquery.tablesorter.pager.js',
            'htdocs/js/watchlist.js',
            'templates/watchlist.html',
        ],
    },
    description = "Watchlist Plugin for Trac v0.12",
    url = 'http://www.trac-hacks.org/wiki/WatchlistPlugin',
    download_url = 'http://trac-hacks.org/svn/watchlistplugin/releases/',
    license      = 'GPLv3',
    zip_safe     = False,
    keywords = 'trac watchlist wiki plugin',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins':
      ['tracwatchlist.plugin = tracwatchlist.plugin']}
)
