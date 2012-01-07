#!/usr/bin/env python

from setuptools import setup, find_packages

PACKAGE = 'DiaVisViewPlugin'
VERSION = '0.1'

setup(  name=PACKAGE, version=VERSION,
        author = 'arkemp, Christopher Lenz,  followed by Robert Martin',
        author_email = 'robert.martin@arqiva.com',
        url = '',
        description = 'Renders Dia and vdx files to png',
        license='BSD',

        package_dir = { 'DiaVisView' : 'DiaVisView'},
        packages = ['DiaVisView'],
        package_data = { 'DiaVisView' : ['DiaVisView/*', ]},
        entry_points = {'trac.plugins': ['DiaVisView.DiaVisView = DiaVisView.DiaVisView']},
        install_requires = ['']
)
