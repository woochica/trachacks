#!/usr/bin/env python

from setuptools import setup

PACKAGE = 'clients'

setup(name=PACKAGE,
    description='Plugin to allow management of which ticket belong to which client',
    keywords='trac plugin ticket client',
    version='0.1',
    url='http://www.trac-hacks.org/wiki/ClientsPlugin',
    license='http://www.opensource.org/licenses/mit-license.php',
    author='Colin Guthrie',
    author_email='trac@colin.guthr.ie',
    long_description="""
    I'll write this later!
    """,
    packages=[PACKAGE],
    package_data={PACKAGE : ['templates/*.cs']},
    entry_points = {
        'trac.plugins': [
            'clients.api = clients.api',
            'clients.client = clients.client'
        ]
    },
    install_requires=[ 'TracWebAdmin' ])   
    #entry_points={'trac.plugins': '%s = %s' % (PACKAGE, PACKAGE)})


#### AUTHORS ####
## Primary Author:
## Colin Guthrie
## http://colin.guthr.ie/
## trac@colin.guthr.ie
## trac-hacks user: coling
