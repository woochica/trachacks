#!/usr/bin/env python
"""
License: BSD

(c) 2005-2008 ::: Alec Thomas (alec@swapoff.org)
(c) 2009      ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import sys

from setuptools import setup, find_packages

try :
  import crypt
except ImportError :
  test_deps = ['twill', 'fcrypt']
else :
  test_deps = ['twill']

setup(
    name='TracXMLRPC',
    version='1.1.2',
    license='BSD',
    author='Alec Thomas',
    author_email='alec@swapoff.org',
    maintainer='Odd Simon Simonsen',
    maintainer_email='simon-code@bvnetwork.no',
    url='http://trac-hacks.org/wiki/XmlRpcPlugin',
    description='RPC interface to Trac',
    zip_safe=True,
    test_suite = 'tracrpc.tests.test_suite',
    tests_require = test_deps,
    packages=find_packages(exclude=['*.tests']),
    package_data={
        'tracrpc': ['templates/*.html', 'htdocs/*.js', 'htdocs/*.css']
        },
    entry_points={
        'trac.plugins': 'TracXMLRPC = tracrpc'
        },
    )
