#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='TracXMLRPC',
    version='1.0.2',
    license='BSD',
    author='Alec Thomas',
    author_email='alec@swapoff.org',
    url='http://trac-hacks.org/wiki/XmlRpcPlugin',
    description='XML-RPC interface to Trac',
    zip_safe=True,
    packages=find_packages(exclude=['*.tests']),
    package_data={
        'tracrpc': ['templates/*.html']
        },
    entry_points={
        'trac.plugins': 'TracXMLRPC = tracrpc'
        },
    )
