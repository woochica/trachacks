#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

extra = {}

try:
    import babel
    extra['message_extractors'] = {
        'tracdragdrop': [
            ('**.py', 'python', None),
            ('**.html', 'genshi', None),
        ],
    }
    from trac.util.dist import get_l10n_js_cmdclass
    extra['cmdclass'] = get_l10n_js_cmdclass()
except ImportError:
    pass

setup(
    name = 'TracDragDrop',
    version = '0.12.0.8',
    description = 'Add drag-and-drop attachments feature to Trac',
    license = 'BSD', # the same as Trac
    url = 'http://trac-hacks.org/wiki/TracDragDropPlugin',
    author = 'Jun Omae',
    author_email = 'jun66j5@gmail.com',
    install_requires = ['Trac >= 0.12'],
    packages = find_packages(exclude=['*.tests*']),
    package_data = {
        'tracdragdrop' : [
            'htdocs/*.js', 'htdocs/*.css', 'htdocs/*.gif', 'templates/*.html',
            'htdocs/messages/*.js',
            'locale/*/LC_MESSAGES/tracdragdrop.mo',
        ],
    },
    entry_points = {
        'trac.plugins': [
            'tracdragdrop.web_ui = tracdragdrop.web_ui',
        ],
    },
    **extra)
