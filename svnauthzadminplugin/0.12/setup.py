#!/usr/bin/env python

from setuptools import setup, find_packages

PACKAGE = 'SvnAuthzAdminPlugin'
VERSION = '0.1.2 (Moved to Trac 0.11)'

setup(  name=PACKAGE, version=VERSION,
        author = 'Gergely Kis',
        author_email = 'trac@kisgergely.com',
        url = 'http://www.trac-hacks.org/wiki/SvnAuthzAdminPlugin',
        description = 'SvnAuthz File Administration Plugin for Trac',
        license='GPL',

        package_dir = { 'svnauthz' : 'svnauthz', 
			'svnauthz_test' : 'svnauthz_test' },
        packages = ['svnauthz', 'svnauthz_test' ],
        package_data = { 'svnauthz' : ['templates/*', ]},
        entry_points = {'trac.plugins': ['svnauthz.admin_ui = svnauthz.admin_ui',
#					 'svnauthz.SvnAuthzFile = svnauthz.SvnAuthzFile'
					 ]},
	zip_safe = False,
        install_requires = []
)
