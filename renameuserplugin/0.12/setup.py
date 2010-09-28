#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
$Id$
"""

from setuptools import setup

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
            'tracrenameuser': extractors,
        }
except ImportError:
    pass

setup(
    name = 'TracRenameUserPlugin',
    version = '0.1',
    description = "Trac plugin to rename users",
    keywords = 'trac user name rename plugin',
    author = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    url = 'http://www.trac-hacks.org/wiki/RenameUserPlugin',
    download_url = 'http://trac-hacks.org/svn/renameuserplugin/releases/',
    license      = 'GPLv3',
    classifiers = ['Framework :: Trac'],
    #install_requires = ['Babel>= 0.9.5', 'Trac >= 0.11'],
    install_requires = ['Trac >= 0.11'],
    packages = ['tracrenameuser'],
    package_data = {
        'tracrenameuser' : [
            'templates/*.html',
        ],
    },
    zip_safe     = False,
    entry_points = {'trac.plugins':
      [
        'tracrenameuser       = tracrenameuser',
        'tracrenameuser.admin = tracrenameuser.admin',
      ]},
    **extra
)
