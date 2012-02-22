#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'PdfImg',
    version = '0.0.2',

    packages = ['PdfImg'],
    include_package_data = True,

    install_requires = ['trac>=0.11'],

    author = "Urs Wihlfahrt",
    author_email = "trac-hacks@wihlfahrt.net",
    description = "Display PDF-Files and vectorgraphics as images in wiki-pages",
    long_description = " Insert PDFs or vectorgraphics like SVGs as PNG-Image into a wikipage. \
    The handling and the parameters are inspired by LaTeX includegraphics. ",
    license = "GPLv2",
    keywords = "trac 0.11 0.12 pdf svg vectorgraphics ",
    url = "http://trac-hacks.org/wiki/PdfImagePlugin",
    entry_points = {
        'trac.plugins': [
            'PdfImg.PdfImg = PdfImg.PdfImg'
        ],
    },

    zip_safe = True
)
