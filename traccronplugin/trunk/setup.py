# -*- encoding: UTF-8 -*-
'''
Created on 18 nov. 2010

@author: thierry
'''

import ez_setup
ez_setup.use_setuptools()

from setuptools import find_packages, setup

setup(name='gomedia',
      version='0.1',
      package_dir = {'': 'src'},
      packages= find_packages('src'),               
      scripts=['scripts/gomusic','scripts/govideo'],
      author='Thierry Bressure',
      author_email='thierry@bressure.net',
      maintainer='Thierry Bressure',
      maintainer_email='thierry@bressure.net',
      description='Update N900 content with media from desktop',
      long_description='Gomedia consist in 2 parts. The N900 part update N900 content with playlist created by desktop part',
      classifiers=[          
          'Programming Language :: Python',
          'Development Status :: 4 - Beta',
          'Topic :: Utilities',
          'Topic :: Multimedia'
          ],
       zip_safe=False


      )
