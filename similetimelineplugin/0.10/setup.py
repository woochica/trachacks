#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracSimileTimeline',
    version = '0.1',
    packages = ['stimeline'],
    package_data={ 'stimeline' : [ 'templates/*.cs', 'htdocs/js/simile/*' ] },
    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "Enhanced timeline using the Simile Timeline.",
    license = "BSD",
    keywords = "trac plugin simile simile",
    url = "http://trac-hacks.org/wiki/SimileTimelinePlugin",

    entry_points = {
        'trac.plugins': [
            'stimeline.web_ui = stimeline.web_ui',
        ],
    },

    install_requires = [ 'TracWebAdmin' ],
)
