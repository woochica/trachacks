# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Verigy (Singapore) Pte. Ltd.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
from setuptools import find_packages, setup

setup(
    name="WikiForms",
    description='Provides forms on any page with a wiki',
    long_description = """
This plugin provides forms on any page with a wiki.
Based on ideas from TracFormsPlugin.
""",
    version="0.1",
    author='Verigy (Singapore) Pte. Ltd., Klaus.Welch@verigy.com',
    license='BSD',
    packages=['wikiforms'],
    entry_points = {
                    'trac.plugins': [
                                      'wikiforms.macros = wikiforms.macros',
                                    ]
                   }
    )

