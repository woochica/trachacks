# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

PACKAGE = 'TracCodeReviewer'
VERSION = '0.0.1'

setup(
    name=PACKAGE, version=VERSION,
    description='Reviews changesets and updates ticket with results',
    author="Rob Guttman", author_email="guttman@alum.mit.edu",
    license='GPL', url='http://trac-hacks.org/wiki/TracCodeReviewerPlugin',
    packages = ['coderev'],
    package_data = {'coderev':['templates/*.html',
                               'htdocs/*.css',
                               'htdocs/*.js',
                               'upgrades/*.py']},
    entry_points = {'trac.plugins':['coderev.api = coderev.api',
                                    'coderev.web_ui = coderev.web_ui',]}
)
