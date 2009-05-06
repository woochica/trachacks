"""
Copyright (C) 2008 Prognus Software Livre - www.prognus.com.br
Author: Diorgenes Felipe Grzesiuk <diorgenes@prognus.com.br>
"""

from setuptools import setup

setup(
    name = 'TracWikiToPdf',
    version = '2.1',
    packages = ['wikitopdf'],
    package_data={ 'wikitopdf' : [ 'templates/*.cs' ] },
    author = "Diorgenes Felipe Grzesiuk",
    author_email = "diorgenes@prognus.com.br",
    description = "Generating PDF files from Wiki pages",
    long_description = "WikiToPdf was developed based on the work of coderanger and athomas. WikiToPdf combines the functionality of CombineWikiPlugin and PagetoPdfPlugin on only one plugin and allows one to setup a template file used to generate the PDF file with a cover and a licence page, for example. ",
    license = "GPL",
    keywords = "trac plugin wiki pdf",
    url = "http://trac-hacks.org/wiki/TracWikiToPdfPlugin",
    classifiers = [
        'Framework :: Trac',
    ],

    entry_points = {
        'trac.plugins': [
            'wikitopdf.formats   = wikitopdf.formats',
            'wikitopdf.web_ui    = wikitopdf.web_ui',
            'wikitopdf.wikitopdf = wikitopdf.wikitopdf',
        ],
    },

    install_requires = [ 'TracWebAdmin' ],
    
)
