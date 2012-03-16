"""
Copyright (C) 2010 Polar Technologies - www.polartech.es
Author: Alvaro Iradier <alvaro.iradier@polartech.es>
"""
from setuptools import setup

NAME = "PlantUML"
VERSION = 1.3

setup(
    name = NAME,
    version = VERSION,
    packages = ['plantuml'],
    author = "Alvaro J. Iradier",
    author_email = "alvaro.iradier@polartech.es",
    maintainer = "Ryan J Ollos",
    maintainer_email = 'ryan.j.ollos@gmail.com',
    description = "A macro to include diagrams from PlantUML",
    license = "GPL",
    keywords = "trac macro uml plantuml embed include",
    url = "http://trac-hacks.org/wiki/PlantUmlMacro",
    entry_points = {
        "trac.plugins": [
            "plantuml.macro = plantuml.macro"
        ]
    }
)
