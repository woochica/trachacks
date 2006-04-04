from setuptools import setup

PACKAGE = 'tractab'
VERSION = '0.1'

setup(name=PACKAGE,
      version=VERSION,
      packages=['tractab'],
      package_data={'tractab' : ['templates/*.cs']},
      entry_points={'trac.plugins': '%s = tractab' % PACKAGE},
)
