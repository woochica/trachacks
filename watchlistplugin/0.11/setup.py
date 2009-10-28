#!/usr/bin/env python

from setuptools import setup
from tracwatchlist.plugin import __revision__ as coderev

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int(r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]

rev = str( max( coderev, __revision__ ) )

setup(
    name = 'TracWatchlistPlugin',
    version = '0.3.' + rev,
    packages = ['tracwatchlist'],
    author = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    package_data = {
        'tracwatchlist' : [ 'templates/*.html', 'htdocs/css/*.css', 
          'htdocs/ico/*', 'htdocs/js/*.js'],
    },
    description = "Watchlist Plugin for Trac",
    url = 'http://www.trac-hacks.org/wiki/WatchlistPlugin',
    license = 'GPLv3',
    keywords = 'trac watchlist wiki plugin',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins':
      ['tracwatchlist.plugin = tracwatchlist.plugin']}
)
