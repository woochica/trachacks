"""
Copyright (C) 2009 Polar Technologies - www.polartech.es
Author: Alvaro Iradier <alvaro.iradier@polartech.es>
"""

from setuptools import setup

setup(
    name = 'TracWikiPrintPlugin',
    version = '1.9.0',
    packages = ['wikiprint'],
    package_data={ 'wikiprint' : [ 'templates/*', 'htdocs/js/*' ] },
    author = "Alvaro J. Iradier",
    author_email = "alvaro.iradier@polartech.es",
    description = "Generating PDF files or printable HTML from Wiki pages",
    long_description = "WikiPrintPlugin was developed based on the work of coderanger, athomas and diorgenes (WikiToPdf). It improves WikiToPdfPlugin to use a pure python library (xhtml2pdf/PISA) to generate PDF files. ",
    license = "GPL",
    keywords = "trac plugin wiki pdf",
    url = "http://trac-hacks.org/wiki/TracWikiPrintPlugin",

    entry_points = {
        'trac.plugins': [
            'wikiprint.formats   = wikiprint.formats',
            'wikiprint.web_ui    = wikiprint.web_ui',
            'wikiprint.wikiprint = wikiprint.wikiprint',
        ],
    },
    
    install_requires = [ 'Trac', 'pisa', 'PIL', 'html5lib', 'reportlab>=2.2' ],
    
)
