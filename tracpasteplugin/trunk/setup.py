# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Armin Ronacher <armin.ronacher@active-4.com>
# Copyright (C) 2008 Michael Renzmann <mrenzmann@otaku42.de>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup

PACKAGE = 'TracPaste'
VERSION = '0.2.2'

setup(
    name=PACKAGE,
    version=VERSION,
    description='Pastebin plugin for Trac',
    author='Armin Ronacher',
    author_email='armin.ronacher@active-4.com',
    maintainer='Michael Renzmann',
    maintainer_email='mrenzmann@otaku42.de',
    url='http://trac-hacks.org/wiki/TracPastePlugin',
    license='BSD',
    packages=['tracpaste'],
    classifiers=[
        'Framework :: Trac',
        'License :: OSI Approved :: BSD License',
    ],
    package_data = {'tracpaste': [
        'templates/*.html',
        'htdocs/css/*.css',
        'htdocs/*.png']
    },
    entry_points = {'trac.plugins': [
        'tracpaste.db = tracpaste.db',
        'tracpaste.model = tracpaste.model',
        'tracpaste.web_ui = tracpaste.web_ui'],
    },
    install_requires = ['Pygments'],
    test_suite = 'tracpaste.tests.test_suite',
    tests_require = []
)
