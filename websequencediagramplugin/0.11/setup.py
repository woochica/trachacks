#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = "SequenceDiagram",
    version = "1.0",
    packages = ["sequencediagram"],
    package_data = {"sequencediagram": []},

    author = "Travis Cox",
    author_email = "cox@inductiveautomation.com",
    description = "A macro to include sequence diagrams from websequencediagrams.com",
    license = "BSD",
    keywords = "trac macro sequence diagram",
    url = "http://www.inductiveautomation.com",

    entry_points = {
        "trac.plugins": [
            "sequencediagram.macro = sequencediagram.macro"
        ]
    }
)
