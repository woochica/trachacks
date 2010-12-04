from setuptools import setup

PACKAGE = 'WikiInclude'
VERSION = '0.2'
DESCRIPTION = 'Page include plugin for Trac Wiki'

setup(
    name=PACKAGE,
    version=VERSION,
    packages=['wikiinclude'],

    entry_points = {
        'trac.plugins': [
            'wikiinclude.macros = wikiinclude',
        ]
    }
)
