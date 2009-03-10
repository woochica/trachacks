#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'TracWatchlistPlugin',
    version = '0.1',
    packages = ['tracwatchlist'],
    author = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    package_data = {
        'tracwatchlist' : [ 'templates/*.html', 'htdocs/css/*.css',],
    },
    description = "Watchlist Plugin for Trac",
    url = 'http://www.trac-hacks.org/wiki/WatchlistPlugin',
    license = 'BSD',
    keywords = 'trac watchlist wiki plugin',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['tracwatchlist.plugin = tracwatchlist.plugin']}
)
