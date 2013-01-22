#!/usr/bin/python

from setuptools import find_packages, setup

setup(
    name='TracComponentAliasPlugin',
    version='0.1.1',
    keywords='trac plugin ticket component alias',
    author='Zack Shahan',
    author_email='zshahan@dig-inc.net',
    url='null',
    description='Trac Component Alias Plugin',
    long_description="""
This plugin for Trac 0.12/1.0 provides a way to map components to a friendly name in the ticket form.
""",
    license='BSD',

    install_requires=['Trac >= 0.12dev'],

    packages=['traccomponentalias'],

    entry_points={
        'trac.plugins': [
            'traccomponentalias.api = traccomponentalias.api',
        ],
    },
)
