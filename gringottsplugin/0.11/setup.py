#!/usr/bin/env python

from setuptools import setup

PACKAGE = 'gringotts'

setup(name=PACKAGE,
    description='Plugin to store and display secure snippets of information (e.g. passwords) in wiki content',
    keywords='trac plugin wiki secure acl',
    version='0.1',
    url='http://www.trac-hacks.org/wiki/GringottsPlugin',
    license='http://opensource.org/licenses/gpl-license.php',
    author='Colin Guthrie',
    author_email='trac@colin.guthr.ie',
    long_description="""
    I'll write this later!
    """,
    packages=[PACKAGE],
    package_data={PACKAGE : ['templates/*.cs', 'htdocs/*.css', 'htdocs/*.gif']},
    entry_points = {
        'trac.plugins': [
            'gringotts.api = gringotts.api',
            'gringotts.webui = gringotts.webui',
            'gringotts.wiki = gringotts.wiki'
        ]
    })

#### AUTHORS ####
## Primary Author:
## Colin Guthrie
## http://colin.guthr.ie/
## trac@colin.guthr.ie
## trac-hacks user: coling
