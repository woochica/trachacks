#!/usr/bin/env python
"""
License: BSD

(c) 2005-2008 ::: Alec Thomas (alec@swapoff.org)
(c) 2009      ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

from setuptools import setup, find_packages

setup(
    name='TracXMLRPC',
    version='1.0.5',
    license='BSD',
    author='Alec Thomas',
    author_email='alec@swapoff.org',
    maintainer='Odd Simon Simonsen',
    maintainer_email='simon-code@bvnetwork.no',
    url='http://trac-hacks.org/wiki/XmlRpcPlugin',
    description='XML-RPC interface to Trac',
    zip_safe=True,
    test_suite = 'tracrpc.tests.suite',
    packages=find_packages(exclude=['*.tests']),
    package_data={
        'tracrpc': ['templates/*.html']
        },
    entry_points={
        'trac.plugins': 'TracXMLRPC = tracrpc'
        },
    )
