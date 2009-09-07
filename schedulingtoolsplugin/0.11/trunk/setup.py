#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'SchedulingTools',
    author = 'Joerg Viola',
    author_email = 'viola@objectcode.de',
    description = 'Trac plugin for scheduling tickets',
    version = '0.1',
    license='BSD',
    packages=['schedulingtools'],
    package_data = { 'schedulingtools': ['templates/*.html'] },
    entry_points = {
        'trac.plugins': [
            'schedulingtools = schedulingtools'
        ]
    }
)
