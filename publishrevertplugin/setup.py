from setuptools import setup

PACKAGE = 'TracSetChangeset'
VERSION = '0.1'

setup(name=PACKAGE,
      version=VERSION,
      packages=['setchangeset'],
      package_data={'setchangeset' : ['templates/*.cs']},
      entry_points={'trac.plugins': '%s = setchangeset' % PACKAGE},
)
