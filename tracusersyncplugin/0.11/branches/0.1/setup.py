#!/usr/bin/env python

from setuptools import find_packages, setup

version='0.1'

setup(name='TracUserSyncPlugin',
      version=version,
      description="Synchronize User Account data between multiple Trac projects",
      author='Andreas Itzchak Rehberg',
      author_email='izzysoft@qumran.org',
      url='http://trac-hacks.org/wiki/izzy',
      keywords='trac plugin',
      license="GPL",
      install_requires = [ 'Trac>=0.11', 'Trac<0.12', 'TracAccountManager' ],
      packages=find_packages(exclude=['ez_setup', 'examples', '*tests*']),
      include_package_data=True,
      package_data={ 'tracusersync': [
          'templates/*.html',
          'htdocs/css/*.css',
          'htdocs/js/*.js',
          ] },
      zip_safe=False,
      entry_points={'trac.plugins': [
            'tracusersync.api = tracusersync.api',
            'tracusersync.web_ui = tracusersync.web_ui'
            ]},
      )

