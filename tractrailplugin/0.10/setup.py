from setuptools import setup

PACKAGE = 'TracTrail'
VERSION = '1.0'

setup(name=PACKAGE,
      version=VERSION,
      packages=['tractrail'],
      entry_points={'trac.plugins': '%s = tractrail' % PACKAGE},
)
