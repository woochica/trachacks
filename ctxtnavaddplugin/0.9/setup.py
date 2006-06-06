#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'CtxtnavAdd',
    version = '0.01',
    packages = ['ctxtnavadd'],
    package_data={
        'ctxtnavadd' : [ 'templates/*.cs' , 'htdocs/js/*.js' ],
    },

    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "Allow adding to the ctxtnav bar of other plugins.",
    license = "BSD",
    keywords = "ctxtnav add ",
    url = "http://trac-hacks.org",

    entry_points = {
        'trac.plugins': [
            'ctxtnavadd.web_ui = ctxtnavadd.web_ui',
        ],
    }
)
