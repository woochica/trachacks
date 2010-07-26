#!/usr/bin/env python

# Copyright 2010 Matthew Noyes <thecodingking at gmail.com>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

latest = '0.1'

status = {
            'planning' :  "Development Status :: 1 - Planning",
            'pre-alpha' : "Development Status :: 2 - Pre-Alpha",
            'alpha' :     "Development Status :: 3 - Alpha",
            'beta' :      "Development Status :: 4 - Beta",
            'stable' :    "Development Status :: 5 - Production/Stable",
            'mature' :    "Development Status :: 6 - Mature",
            'inactive' :  "Development Status :: 7 - Inactive"
         }
dev_status = status["beta"]

cats = [
    dev_status,
    
      "Environment :: Plugins", 
      "Environment :: Web Environment", 
      "Framework :: Trac", 
      "Intended Audience :: Developers", 
      "Intended Audience :: Information Technology", 
      "Intended Audience :: Other Audience", 
      "Intended Audience :: System Administrators", 
      "License :: OSI Approved :: Apache Software License", 
      "Operating System :: OS Independent", 
      "Programming Language :: Python", 
      "Programming Language :: Python :: 2.5", 
      "Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries", 
      "Topic :: Internet :: WWW/HTTP :: HTTP Servers", 
      "Topic :: Internet :: WWW/HTTP :: WSGI", 
      "Topic :: Software Development :: Bug Tracking", 
      "Topic :: Software Development :: Libraries :: Application Frameworks", 
      "Topic :: Software Development :: Libraries :: Python Modules", 
    ]

# Be compatible with older versions of Python
from sys import version
if version < '2.2.3':
    from distutils.dist import DistributionMetadata
    DistributionMetadata.classifiers = None
    DistributionMetadata.download_url = None

DIST_NM = 'TracCollapsiblePlugin'
PKG_INFO = {'traccollapsible' : ('traccollapsible',                     # Package dir
                                 # Package data
                                 ['../CHANGES', '../TODO', '../COPYRIGHT', 
                                  '../NOTICE', '../README'],
                                 ), 
            }

ENTRY_POINTS = r"""
               [trac.plugins]
               traccollapsible = traccollapsible
               """

setup(
	name=DIST_NM,
	version=latest,
	description='Embed wiki-text in a foldable structure, trac ticket attachment style',
	author='Matthew Noyes',
	author_email='thecodingking@gmail.com',
	maintainer='Matthew Noyes',
	maintainer_email='thecodingking@gmail.com',
        url = 'http://trac-hacks.org/wiki/CollapsiblePlugin',
	requires = ['trac',  'trac', ],
        install_requires = [
        'setuptools>=0.6b1',
        'Trac>=0.11',
        ],
	package_dir = dict([p, i[0]] for p, i in PKG_INFO.iteritems()),
	packages = PKG_INFO.keys(),
	package_data = dict([p, i[1]] for p, i in PKG_INFO.iteritems()),
	include_package_data=True,
	provides = ['%s (%s)' % (p, latest) for p in PKG_INFO.keys()],
	entry_points = ENTRY_POINTS,
	classifiers = cats,
	)
