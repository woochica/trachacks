#!/usr/bin/env python

from setuptools import find_packages, setup

version='0.1'

setup(name='LogViewerPlugin',
      version=version,
      description="View Trac log files from within the Web-UI",
      author='Andreas Itzchak Rehberg',
      author_email='izzysoft@qumran.org',
      url='http://trac-hacks.org/wiki/izzy',
      keywords='trac plugin log',
      license="GPL",
      install_requires = [ 'Trac>=0.11', 'Trac<0.12' ],
      packages=find_packages(exclude=['ez_setup', 'examples', '*tests*']),
      include_package_data=True,
      package_data={ 'logviewer': [
          'templates/*.html',
          'htdocs/css/*.css',
          ] },
      zip_safe=True,
      entry_points={'trac.plugins': [
            'logviewer.api = logviewer.api',
            'logviewer.web_ui = logviewer.web_ui'
            ]},
      )

