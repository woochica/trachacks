#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
import os

from setuptools import setup, find_packages

extra = {}

try:
    from trac.util.dist import get_l10n_cmdclass
    cmdclass = get_l10n_cmdclass()
    if cmdclass: # Yay, Babel is there, we've got something to do!
        extra['cmdclass'] = cmdclass
        extractors = [
            ('**.py', 'python', None),
        ]
        extra['message_extractors'] = {
            'ticketchangesets': extractors,
        }
except ImportError, e:
    print e
    pass

setup(
    name = 'TracTicketChangesets',
    version = '1.0',
    description = 'Relates tickets and changesets based on commit messages.',
    long_description = open(os.path.join(os.path.dirname(__file__),
                                         'README')).read(),
    author = 'Mikael Relbe',
    author_email = 'mikael@relbe.se',
    license = 'BSD',
    url = 'http://trac-hacks.org/wiki/TracTicketChangesetsPlugin',
    classifiers = [
        'Environment :: Web Environment',
        'Framework :: Trac',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],

    packages = find_packages(exclude=['*.tests']),
    package_data = {
        'ticketchangesets': [
            'locale/*.*',
            'locale/*/LC_MESSAGES/*.mo'
        ],
    },
    
    keywords = 'trac plugin ticket commit message changesets',
    
    zip_safe = True,
    
    install_requires = ['Trac >= 0.12dev'],
    
    extras_require = {
        'Babel': ['Babel>=0.9.5'],
    },
    
    entry_points = """
        [trac.plugins]
        ticketchangesets.admin = ticketchangesets.admin
        ticketchangesets.init = ticketchangesets.init
        ticketchangesets.commit_updater = ticketchangesets.commit_updater
        ticketchangesets.web_ui = ticketchangesets.web_ui
    """,
    
    **extra
)
