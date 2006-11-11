from setuptools import setup

PACKAGE = 'TracSetChangeset'
VERSION = '0.2'

setup(name=PACKAGE,
      version=VERSION,
      packages=['setchangeset','publish'],
      package_data={'setchangeset' : ['templates/*.cs'], 'publish' : ['templates/*.cs']},
      entry_points={'trac.plugins': '%s = setchangeset' % PACKAGE, 'trac.plugins': '%s = publish' % PACKAGE},
)
