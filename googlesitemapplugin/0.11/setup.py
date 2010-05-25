#!/usr/bin/env python

from setuptools import setup
from tracgooglesitemap.plugin import __revision__ as coderev

__url__      = ur"$URL: http://trac-hacks.org/svn/listofwikipagesmacro/0.11/setup.py $"[6:-2]
__author__   = ur"$Author: martin_s $"[9:-2]
__revision__ = ur"$Rev: 6958 $"[6:-2]
__date__     = ur"$Date: 2009-10-30 17:51:13 +0000 (Fri, 30 Oct 2009) $"[7:-2]

rev = max(__revision__, coderev)

setup(
    name = 'TracGoogleSitemapPlugin',
    version = '0.1.' + rev,
    packages = ['tracgooglesitemap'],
    author = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description = "Plugin to generate Google Sitemaps (version for Trac 0.11)",
    url = 'http://www.trac-hacks.org/wiki/GoogleSitemapPlugin',
    license      = 'GPLv3',
    zip_safe     = False,
    keywords = 'trac google sitemap plugin',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['tracgooglesitemap = tracgooglesitemap']}
)
