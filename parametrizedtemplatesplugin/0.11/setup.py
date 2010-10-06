"""
Copyright (C) 2009 Polar Technologies - www.polartech.es
Author: Alvaro Iradier <alvaro.iradier@polartech.es>
"""

from setuptools import setup

setup(
    name = 'ParametrizedTemplates',
    version = '0.2',
    packages = ['parametrizedtemplates'],
    package_data={
        'parametrizedtemplates': [
            'htdocs/*.css',
            'htdocs/*.png',
            'htdocs/*.js',
            'templates/*.html'
        ]
    },

    author = "Alvaro J. Iradier",
    author_email = "alvaro.iradier@polartech.es",
    description = "Create pages from templates with parameters, using a form to input the parameter values.",
    license = "GPL",
    keywords = "trac plugin wiki templates",
    url = "http://trac-hacks.org/wiki/ParametrizedTemplatesPlugin",

    entry_points = {
        'trac.plugins': [
            'parametrizedtemplates.parametrizedtemplates = parametrizedtemplates.parametrizedtemplates',
        ],
    },
    
    install_requires = [ 'Trac', ],
    
)
