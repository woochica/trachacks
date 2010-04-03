from setuptools import setup

PACKAGE = 'TracDrupalIntegration'
VERSION = '0.1'

setup(name=PACKAGE,
      version=VERSION,
      packages=['drupalintegration'],
      entry_points={'trac.plugins': '%s = drupalintegration' % PACKAGE},
)
