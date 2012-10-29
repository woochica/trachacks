#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

setup(
    name = "MilestoneQuery",
    version = 1.0,
    packages = find_packages(exclude=['*.tests']),
    author = "Nic Ferrier",
    description = "List milestones.",
    keywords = "trac macro milestone",
    url = "http://trac-hacks.org/wiki/MilestoneQueryMacro",
    entry_points = {
        "trac.plugins": [
            "MilestoneQuery = milestonequery.macro"
        ]
    }
)
