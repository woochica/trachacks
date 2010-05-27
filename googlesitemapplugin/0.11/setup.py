#!/usr/bin/env python

from setuptools import setup
from tracgooglesitemap.plugin import __revision__ as codereva
from tracgooglesitemap.notify import __revision__ as coderevb

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = ur"$Rev$"[6:-2]
__date__     = ur"$Date$"[7:-2]

rev = max(__revision__, codereva, coderevb)

setup(
    name = 'TracGoogleSitemapPlugin',
    version = '1.0.' + rev,
    packages = ['tracgooglesitemap'],
    author = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description = "Plugin to generate Google Sitemaps (version for Trac 0.11)",
    url = 'http://www.trac-hacks.org/wiki/GoogleSitemapPlugin',
    license      = 'GPLv3',
    zip_safe     = False,
    keywords = 'trac google sitemap plugin',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['tracgooglesitemap.plugin = tracgooglesitemap.plugin', 'tracgooglesitemap.notify = tracgooglesitemap.notify']}
)
