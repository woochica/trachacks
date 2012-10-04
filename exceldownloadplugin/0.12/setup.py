#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

extra = {}
try:
    import babel
    extra['message_extractors'] = {
        'tracexceldownload': [
            ('**/*.py',              'python', None),
            ('**/templates/**.html', 'genshi', None),
        ],
    }
    from trac.util.dist import get_l10n_cmdclass
    extra['cmdclass'] = get_l10n_cmdclass()
except ImportError:
    pass

setup(
    name = 'ExcelDownloadPlugin',
    version = '0.12.0.3',
    description = 'Allow to download query and report page as Excel',
    license = 'BSD', # the same as Trac
    packages = find_packages(exclude=['*.tests*']),
    package_data = {
        'tracexceldownload': [
            'locale/*.*', 'locale/*/LC_MESSAGES/*.mo',
        ],
    },
    install_requires = ['Trac >= 0.12', 'xlwt'],
    entry_points = {
        'trac.plugins': [
            'tracexceldownload.ticket = tracexceldownload.ticket',
            'tracexceldownload.translation = tracexceldownload.translation',
        ],
    },
    **extra)
