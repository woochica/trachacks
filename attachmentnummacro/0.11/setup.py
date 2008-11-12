#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'TracAttachmentNumMacro',
    version = '0.5',
    packages = ['tracattachmentnum'],
    author = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description = "Trac Macro to link to local attachments by number.",
    url = 'http://www.trac-hacks.org/wiki/AttachmentNumMacro',
    license = 'GPLv3',
    keywords = 'trac attachment number macro',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['tracattachmentnum = tracattachmentnum']}
)
