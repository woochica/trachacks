#!/usr/bin/env python

from setuptools import setup

PACKAGE = 'cc_selector'

setup(
    name = PACKAGE,
    version = '0.0.2',
    description = 'Visual Cc ticket field editor for Trac',
    keywords = 'trac cc ticket editor',
    url = 'http://trac-hacks.org/wiki/CcSelectorPlugin',
    author = 'Vladislav Naumov',
    author_email = 'vnaum@vnaum.com',
    license = 'GPL',
    maintainer = 'Steffen Hoffmann',
    maintainer_email = 'hoff.st@web.de',
    packages = [PACKAGE],
    package_data = {PACKAGE: ['htdocs/*', 'templates/*']},
    zip_safe = True,
    entry_points = {
        'trac.plugins': [
            'cc_selector.cc_selector = cc_selector.cc_selector'
        ]},
    install_requires = ['Genshi >= 0.5', 'Trac >= 0.11'],
    )
