#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

extra = {}
try:
    import babel
    extra['message_extractors'] = {
        'tracstickyticket': [
            ('**.py', 'python', None),
            ('**.html', 'genshi', None),
        ],
    }
    from trac.util.dist import get_l10n_cmdclass
    extra['cmdclass'] = get_l10n_cmdclass()
except ImportError:
    pass

setup(
    name = 'StickyTicketPlugin',
    version = '0.12.0.3',
    description = 'Print Ticket on Sticky',
    license = 'BSD', # the same license as Trac
    url = 'http://trac-hacks.org/wiki/StickyTicketPlugin',
    author = 'Jun Omae',
    author_email = 'jun66j5@gmail.com',
    install_requires = [
        'reportlab',
    ],
    packages = find_packages(exclude=['*.tests*']),
    package_data = {
        'tracstickyticket': [
            'locale/*/LC_MESSAGES/*.mo',
        ]
    },
    entry_points = {
        'trac.plugins': [
            'tracstickyticket.web_ui = tracstickyticket.web_ui',
        ],
    },
    **extra)
