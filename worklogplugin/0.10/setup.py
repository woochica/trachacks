#!/usr/bin/env python

from setuptools import setup

PACKAGE = 'worklog'

setup(name=PACKAGE,
      description='Plugin to manage the which tickets users are currently working on',
      keywords='trac plugin ticket working',
      version='0.1',
      url='',
      license='http://www.opensource.org/licenses/mit-license.php',
      author='Colin Guthrie',
      author_email='trac@colin.guthr.ie',
      long_description="""
      I'll write this later!
      """,
      packages=[PACKAGE],
      package_data={PACKAGE : ['templates/*.cs', 'htdocs/*.css', 'htdocs/*.png', 'htdocs/*.js']},
      entry_points={'trac.plugins': '%s = %s' % (PACKAGE, PACKAGE)},
      install_requires=[ 'TracWebAdmin' ])


#### AUTHORS ####
## Primary Author:
## Colin Guthrie
## http://colin.guthr.ie/
## trac@colin.guthr.ie
## trac-hacks user: coling

