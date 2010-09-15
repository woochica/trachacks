#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
    version = '0.6',
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
        ],
    },
    zip_safe     = False,
    entry_points = {'trac.plugins':
      [
        'tracwatchlist = tracwatchlist',
        'tracwatchlist.plugin = tracwatchlist.plugin',
        'tracwatchlist.db = tracwatchlist.db',
        'tracwatchlist.nav = tracwatchlist.nav',
        'tracwatchlist.render = tracwatchlist.render',
        'tracwatchlist.translation = tracwatchlist.translation',
      ]},
    **extra
)
