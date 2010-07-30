#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'TracNoticeManager',
    version = '0.1.2',
    author = 'Carsten Tittel',
    author_email = 'carsten.tittel@fokus.fraunhofer.de',
    url = 'https://trac-hacks.org/wiki/NoticeManagerPlugin',
    description = 'User email management plugin for Trac',

    license = 'BSD',
    zip_safe=True,
    packages=['notice_mgr'],
    package_data={'notice_mgr': ['templates/*.cs']},

    entry_points = {
        'trac.plugins': [
            'notice_mgr.admin = notice_mgr.admin'
        ]
    }
)
