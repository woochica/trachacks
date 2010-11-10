#!/usr/bin/env python

from setuptools import setup

setup(
    name='TracRemoteTicket', 
    version='0.1',
    description='Link trac tickets to others in remote Trac instances',
    long_description='',
    
    author='',
    author_email='',
    
    url='http://trac-hacks.org/wiki/RemoteTicketPlugin',
    classifiers=[],
    license='',
    
    install_requires = [
        'Trac>=0.12',
        ],
    
    packages=['tracremoteticket'],
    package_data={
       'tracremoteticket': [
            'templates/*.html',
            'htdocs/js/*.js',
            'htdocs/css/*.css',
            ]
        },
            
    entry_points = {
        'trac.plugins' : [
            'tracremoteticket = tracremoteticket',
            ],
        },
)
