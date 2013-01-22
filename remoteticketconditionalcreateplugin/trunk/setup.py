#!/usr/bin/python

from setuptools import find_packages, setup

setup(
    name='RemoteTicketConditionalCreatePlugin',
    version='0.3.7',
    keywords='trac plugin ticket conditional remote',
    author='Zack Shahan',
    author_email='zshahan@dig-inc.net',
    url='null',
    description='Trac Remote Ticket Conditional Create Plugin',
    long_description="""
This plugin for Trac 0.12/1.0 provides Ticket escalation functionality.

Allows ticket linking via "escalating" between trac environments on same instance.
""",
    license='BSD',

    install_requires=['Trac >= 0.12dev', 'TracXmlRpc'],

    packages=['remoteticketconditionalcreate'],

    entry_points={
        'trac.plugins': [
            'remoteticketconditionalcreate.api = remoteticketconditionalcreate.api',
        ],
    },
)
