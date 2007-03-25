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
    package_data={
        'tracrpc': [
            'templates/*.cs',
            'htdocs/js/*.js'
        ]
    },
    entry_points={
        'trac.plugins': [
            'tracrpc.web_ui = tracrpc.web_ui',
            'tracrpc.json_rpc = tracrpc.json_rpc',
            'tracrpc.xml_rpc = tracrpc.xml_rpc',
            'tracrpc.api = tracrpc.api',
            'tracrpc.search = tracrpc.search',
            'tracrpc.ticket = tracrpc.ticket',
            'tracrpc.util = tracrpc.util',
            'tracrpc.wiki = tracrpc.wiki',
        ]
    }
)
