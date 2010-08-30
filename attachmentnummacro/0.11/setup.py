#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + ur"$Rev$"[6:-2])
__date__     = ur"$Date$"[7:-2]



setup(
    name         = 'TracAttachmentNumMacro',
    version      = '0.7',
    packages     = ['tracattachmentnum'],
    author       = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description  = "Trac Macro to link to local attachments by number.",
    url          = 'http://www.trac-hacks.org/wiki/AttachmentNumMacro',
    license      = 'GPLv3',
    zip_safe     = False,
    keywords     = 'trac attachment number macro',
    classifiers  = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['tracattachmentnum.attachmentnum = tracattachmentnum.attachmentnum']}
)
