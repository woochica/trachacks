#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'SixhatsMacro',
    version = '0.1',
    packages = ['sixhats'],
    package_data = {'sixhats': ['htdocs/img/fedora/*.jpg',
                                'htdocs/img/hardhat/*.jpg',
                                'htdocs/img/tophat/*.jpg',
                                'htdocs/img/source/*.svg',
                                'htdocs/js/*.js',
                                'htdocs/pdf/*.pdf',
                                'htdocs/txt/*.txt']},
    author = 'Louis Cordier',
    author_email = 'lcordier@gmail.com',
    description = 'Macro to facilitate the use for Sixhats thinking method, think Scrum meetings.',
    url = '',
    license = 'BSD',
    keywords = 'trac plugin de bono sixhats macro',
    classifiers = ['Framework :: Trac'],    
    entry_points = {'trac.plugins': ['sixhats.macro = sixhats.macro']}
)
