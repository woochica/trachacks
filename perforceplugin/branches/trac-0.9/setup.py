#!/usr/bin/env python

from setuptools import setup, find_packages

TracMercurial = 'http://projects.edgewall.com/trac/wiki/TracMercurial'

setup(
    name='TracPerforce',
    description='Perforce plugin for Trac',
    keywords='trac scm plugin perforce p4',
    version='0.2',
    url='http://trac-hacks.swapoff.org/wiki/PerforcePlugin',
    license='''
    Copyright 2005, Thomas Tresssieres
    Provided "as is"
    ''',
    author='Thomas Tressieres',
    author_email='thomas.tressieres@free.fr',
    long_description="""
    This Trac 0.9+ plugin provides support for the Perforce SCM.
    
    It requires a special development version of Trac, which features
    pluggable SCM backend providers, see %s for more details.
    """ % TracMercurial,
    zip_safe=True,
    packages=['p4trac'],
    entry_points={'trac.plugins': 'p4trac = p4trac.p4trac'})
