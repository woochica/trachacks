#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#
# Copyright (C) 2007 Optaros, Inc
# All rights reserved.

from setuptools import setup

PACKAGE = 'TracSVNPoliciesPlugin'
VERSION = '0.2'

setup(name= PACKAGE, version= VERSION,
      author= "Andrei Culapov", 
      author_email= "aculapov@optaros.com", 
      url= 'http://www.optaros.com/',
      description= 'Policy management for SVN repositories',
      license= 'BSD',
      packages= ['svnpolicies'],
      package_data= {'svnpolicies': ['svnpolicy.conf', 'README','htdocs/css/*.css', 'htdocs/js/*.js', 'templates/*.html', 'hooks/*.py']},
      entry_points= {'trac.plugins': [
            'svnpolicies.admin = svnpolicies.admin',
            ]},
      eager_resources= ['hooks/post-commit.py', 'hooks/pre-commit.py', 'hooks/pre-revprop-change.py', 'hooks/loader.py',],
      zip_safe=True,
)
