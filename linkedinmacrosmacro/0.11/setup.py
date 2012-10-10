#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'LinkedInMacro',
    version = '0.1',
    packages = ['linkedinmacro'],
    author = 'Carlos Peñas San José',
    author_email = 'cpenas@warp.es',
    description = 'macro for Linked-In company widget.',
    license = 'Artistic 2.0',
    url = 'http://public.warp.es/trac-stuff/wiki/Plugins/LinkedInMacro',
    entry_points = {
        'trac.plugins':[
            'linkedinmacro.macro = linkedinmacro.macro'   
        ]
    },
)
