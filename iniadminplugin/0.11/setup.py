#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(name='IniAdmin',
      version='0.3',
      packages=['iniadmin'],
      author='Alec Thomas',
      maintainer='Jun Omae',
      maintainer_email='jun66j5@gmail.com',
      description='Expose all TracIni options using the Trac config option API',
      url='http://trac-hacks.org/wiki/IniAdminPlugin',
      license='BSD',
      entry_points={'trac.plugins': ['iniadmin = iniadmin']},
      package_data={'iniadmin' : ['htdocs/css/*.css', 'templates/*.html', ]},
      test_suite='iniadmin.tests',
)
