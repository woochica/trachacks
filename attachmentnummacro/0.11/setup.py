#!/usr/bin/env python

from setuptools import setup
from tracattachmentnum.attachmentnum import __revision__ as coderev

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]

rev = str( max( coderev, __revision__ ) )

setup(
    name = 'TracAttachmentNumMacro',
    version = '0.5.' + rev,
    packages = ['tracattachmentnum'],
    author = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description = "Trac Macro to link to local attachments by number.",
    url = 'http://www.trac-hacks.org/wiki/AttachmentNumMacro',
    license = 'GPLv3',
    keywords = 'trac attachment number macro',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['tracattachmentnum.attachmentnum = tracattachmentnum.attachmentnum']}
)
