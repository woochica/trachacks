# -*- coding: utf-8 -*-

from setuptools import setup

PACKAGE = 'flexiblereporternotification'

setup(name=PACKAGE,
      version='0.0.1',
      packages=[PACKAGE],
      url='http://trac-hacks.org/wiki/FlexibleReporterNotificationPlugin',
      author='Satyam',
      entry_points={'trac.plugins': '%s = %s' % (PACKAGE, PACKAGE)},
)

