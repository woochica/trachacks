#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

simile_dirs = [
    '/',
    '/ext',
    '/ext/geochrono',
    '/ext/geochrono/images',
    '/ext/geochrono/scripts',
    '/ext/geochrono/scripts/l10n',
    '/ext/geochrono/scripts/l10n/en',
    '/ext/geochrono/styles',
    '/images',
    '/scripts',
    '/scripts/ext',
    '/scripts/l10n',
    '/scripts/l10n/en',
    '/scripts/l10n/es',
    '/scripts/l10n/fr',
    '/scripts/l10n/it',
    '/scripts/l10n/ru',
    '/scripts/l10n/se',
    '/scripts/l10n/vi',
    '/scripts/l10n/zh',
    '/scripts/util',
    '/styles'
]


setup(
    name = 'TracSimileTimeline',
    version = '0.1',
    packages = ['stimeline'],
    package_data={ 'stimeline' : [ 'templates/*.cs', 'htdocs/js/*.js' ] + [ 'htdocs/js/simile'+d+'/*.*' for d in simile_dirs ] },
    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "Enhanced timeline using the Simile Timeline.",
    license = "BSD",
    keywords = "trac plugin simile simile",
    url = "http://trac-hacks.org/wiki/SimileTimelinePlugin",

    entry_points = {
        'trac.plugins': [
            'stimeline.web_ui = stimeline.web_ui',
        ],
    },

    install_requires = [ 'TracWebAdmin' ],
)
