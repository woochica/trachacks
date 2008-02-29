#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#
# Copyright (C) 2008 McMaster University
#
# This software is licensed under the GPLv2 or later, and a copy is available
# in the COPYING, which you should have received as part of this distribution.
# The terms are also available at
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.html.
#
# Author: Servilio Afre Puentes <afrepues@mcmaster.ca>

from setuptools import setup

setup(
    name = 'TracExtendedFieldProperties',
    version = '0.3',
    packages = ['extendedfieldprops'],
    package_data={ 'extendedfieldprops' : [ 'templates/*.cs' ] },

    author = "Servilio Afre Puentes",
    author_email = "afrepues@mcmaster.ca",
    description = "Extended ticket stock and custom fields customization for Trac.",
    long_description = "A Trac plugin that provides more configuration options for ticket fields, both stock and custom fields, like labeling and hiding/skipping.",
    license = "GPLv2",
    keywords = "trac 0.10 plugin ticket customization",
    url = "https://develz.mcmaster.ca/webdev/TracRelabelField",
    classifiers = [
        'Framework :: Trac',
    ],

    entry_points = {
        'trac.plugins': [
            'extendedfieldprops.web_ui = extendedfieldprops.web_ui',
        ],
    }
)
