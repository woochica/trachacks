#!/usr/bin/env python

from setuptools import setup
from tracwatchlist.plugin import __revision__ as coderev

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]

rev = str( max( coderev, __revision__ ) )

setup(
    name = 'TracWatchlistPlugin',
    version = '0.4.' + rev,
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
    description = "Watchlist Plugin for Trac",
    url = 'http://www.trac-hacks.org/wiki/WatchlistPlugin',
    download_url = 'http://trac-hacks.org/svn/watchlistplugin/releases/',
    license      = 'GPLv3',
    zip_safe     = False,
    keywords = 'trac watchlist wiki plugin',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins':
      ['tracwatchlist.plugin = tracwatchlist.plugin']}
)
