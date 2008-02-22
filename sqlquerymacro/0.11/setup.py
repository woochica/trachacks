#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = "SqlQuery",
    version = "0.1",
    packages = ["sqlquery"],
    package_data = {"sqlquery": []},

    author = "James Mills",
    author_email = "James dot Mills at au dot pwc dot com",
    description = "A macro to execute sql queries against a database",
    license = "BSD",
    keywords = "trac macro sql query",
    url = "http://trac-hacks.org/",

    entry_points = {
        "trac.plugins": [
            "sqlquery.macro = sqlquery.macro"
        ]
    }
)
