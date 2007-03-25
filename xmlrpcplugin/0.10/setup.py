#!/usr/bin/env python

from setuptools import setup

setup(
    name='TracXMLRPC',
    version='0.1',
    author='Alec Thomas',
    author_email='alec@swapoff.org',
    url='http://trac-hacks.swapoff.org/wiki/XmlRpcPlugin',
    description='XML-RPC interface to Trac',
    zip_safe=True,
    packages=['tracrpc'],
    package_data={'tracrpc': ['templates/*.cs']},
    entry_points={'trac.plugins': 'TracXMLRPC = tracrpc'},
    )
