#!/usr/bin/env python

from setuptools import find_packages, setup

version='0.2'

setup(name='LogViewerPlugin',
      version=version,
      description="View Trac log files from within the Web-UI",
      long_description="This plugin allows you to view your trac.log logfile without shell access, just via the Web-UI Admin interface. You can select to only display messages from a specified log level (e.g. only warnings), optionally including higher levels. Moreover, you may restrict the output to the latest N lines, and even filter for lines containing a specified string or even matching a regular expression.",
      author='Andreas Itzchak Rehberg',
      author_email='izzysoft@qumran.org',
      url='http://trac-hacks.org/wiki/izzy',
      keywords='trac plugin log',
      license="GPL",
      install_requires = [ 'Trac>=0.11' ],
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
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Web Environment',
          'Framework :: Trac',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Topic :: Software Development :: Bug Tracking',
          'Topic :: System :: Logging',
          'Topic :: System :: Systems Administration',
          ],
      )
