# -*- coding: utf-8 -*-

from setuptools import setup

VERSION = '0.3'

setup(
    name = 'TracForms',
    description = 'Universal form provider for tickets and wiki',
    version = VERSION,
    author='Rich Harkins',
    author_email='rich@worldsinfinite.com',
    maintainer = 'Steffen Hoffmann',
    maintainer_email = 'hoff.st@web.de',
    url = 'http://trac-hacks.org/wiki/TracFormsPlugin',
    license = 'GPL',
    packages = ['tracforms'],
    package_data = {
        'tracforms': [
            'locale/*/LC_MESSAGES/*.mo', 'locale/.placeholder',
        ]
    },
    zip_safe = True,
    install_requires = ['Trac >= 0.11'],
    entry_points = {
        'trac.plugins': [
            'tracforms.api = tracforms.api',
            'tracforms.errors = tracforms.errors',
            'tracforms.formdata = tracforms.formdata',
            'tracforms.formdb = tracforms.formdb',
            'tracforms.macros = tracforms.macros',
            'tracforms.web_ui = tracforms.web_ui',
        ]
    }
)
