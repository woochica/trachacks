#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Polar Technologies - www.polartech.es
# Copyright (C) 2010 Alvaro J Iradier
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup

setup(
    name = "PlantUML",
    version = 1.4,
    packages = ['plantuml'],
    author = "Alvaro J. Iradier",
    author_email = "alvaro.iradier@polartech.es",
    maintainer = "Ryan J Ollos",
    maintainer_email = 'ryan.j.ollos@gmail.com',
    description = "A macro to include diagrams from PlantUML",
    license = "BSD 3-Clause",
    keywords = "trac macro uml plantuml embed include",
    url = "http://trac-hacks.org/wiki/PlantUmlMacro",
    entry_points = {
        "trac.plugins": [
            "plantuml.macro = plantuml.macro"
        ]
    }
)
