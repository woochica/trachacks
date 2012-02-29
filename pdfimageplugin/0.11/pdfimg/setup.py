#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'PdfImg',
    version = '0.0.3',

    packages = ['pdfimg'],
    include_package_data = True,

    install_requires = ['trac>=0.11'],

    author = "Urs Wihlfahrt",
    author_email = "trac-hacks@wihlfahrt.net",
    description = "Display PDF-files and vector graphics as images in wiki-pages",
    long_description = "Insert PDFs or vector graphics like SVGs as PNG-Image into a wiki-page. \
    The handling and the parameters are inspired by LaTeX includegraphics and the trac ImageMacro.",
    license = "GPLv2",
    keywords = "trac 0.11 0.12 pdf svg vectorgraphics",
    url = "http://trac-hacks.org/wiki/PdfImagePlugin",
    entry_points = {
        'trac.plugins': [
            'pdfimg.pdfimg = pdfimg.pdfimg'
        ],
    },

    zip_safe = True
)
