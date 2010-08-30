#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + ur"$Rev$"[6:-2])
__date__     = ur"$Date$"[7:-2]


setup(
    name = 'TracGoogleSitemapPlugin',
    version = '1.0',
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
