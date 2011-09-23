#!/usr/bin/env python

from setuptools import setup

PACKAGE = 'importexportxls'

setup(name='ImportExportXLS',
      description='Plugin to export and import tickets via XLS',
      keywords='ticket excel import export',
      version='0.1.2',
      url='',
      license='http://www.opensource.org/licenses/mit-license.php',
      author='ben.12',
      author_email='',
      long_description="",
      packages=[PACKAGE],
      package_data={PACKAGE : ['templates/*.cs', 'templates/*.html', 'htdocs/*.css', 'htdocs/*.png', 'htdocs/*.js']},
      entry_points={'trac.plugins': '%s = %s' % (PACKAGE, PACKAGE)})
