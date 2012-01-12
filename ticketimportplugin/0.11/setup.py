#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

#
# Copyright (c) 2007-2008 by nexB, Inc. http://www.nexb.com/ - All rights reserved.
# Author: Francois Granade - fg at nexb dot com
# Licensed under the same license as Trac - http://trac.edgewall.org/wiki/TracLicense
#

from setuptools import setup

PACKAGE='talm_importer'

setup(
    name='TicketImport',
    version='0.8.1',
    author='Francois Granade',
    author_email='fg@nexb.com',
    url='http://nexb.com',
    license='BSD',
    description='Import CSV and Excel files',
    zip_safe=True,
    packages=[PACKAGE],
    package_data={PACKAGE: ['templates/*.html']},
    entry_points={'trac.plugins': 'TicketImport = %s' % (PACKAGE)}
    )
