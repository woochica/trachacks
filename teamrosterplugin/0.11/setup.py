#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(name='TracTeamRosterPlugin',
      version='0.1',
      packages=['tracteamroster'],
      author="Catalin Balan", 
      author_email="cbalan@optaros.com", 
      url='http://www.optaros.com/',
      description='Team Roster',
      license='BSD',
      entry_points={'trac.plugins': [
            'tracteamroster.api = tracteamroster.api',
            'tracteamroster.userprofiles_stores = tracteamroster.userprofiles_stores',
            'tracteamroster.admin = tracteamroster.admin',
	        'tracteamroster.prefs = tracteamroster.prefs',
            'tracteamroster.rpc = tracteamroster.rpc',
            'tracteamroster.macros = tracteamroster.macros'
            ]},
      package_data={'tracteamroster' : ['htdocs/js/*.js', 'htdocs/css/*.css', 'templates/*.html','htdocs/img/*.png']},
      install_requires=[],
      test_suite = 'tracteamroster.tests'
      )
