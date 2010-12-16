#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

extra = {}

try:
    from trac.util.dist import get_l10n_cmdclass
    cmdclass = get_l10n_cmdclass()
    if cmdclass:
        extra['cmdclass'] = cmdclass
        extractors = [
            ('**.py',                'python', None),
            ('**/templates/**.html', 'genshi', None),
        ]
        extra['message_extractors'] = {
            'dynfields': extractors,
        }
# i18n is implemented to be optional here
except ImportError:
    pass


PACKAGE = 'TracDynamicFields'
VERSION = '2.1.1'

setup(
    name=PACKAGE, version=VERSION,
    description='Dynamically hide, default, copy, clear, etc. ticket fields',
    author="Rob Guttman", author_email="guttman@alum.mit.edu",
    license='GPL', url='http://trac-hacks.org/wiki/DynamicFieldsPlugin',
    packages = ['dynfields'],
    package_data = {'dynfields': ['templates/*.html', 'htdocs/*.js',
        'locale/*/LC_MESSAGES/*.mo', 'locale/.placeholder']},
    entry_points = {'trac.plugins':['dynfields.rules = dynfields.rules',
                                    'dynfields.web_ui = dynfields.web_ui']},
    install_requires = ['Genshi >= 0.5', 'Trac >= 0.11'],
    extras_require = {'Babel': 'Babel>= 0.9.5', 'Trac': 'Trac >= 0.12'},
    **extra
)
