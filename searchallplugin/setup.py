from setuptools import setup

PACKAGE = 'tracsearchall'
VERSION = '0.4'

setup(name=PACKAGE,
      version=VERSION,
      packages=['tracsearchall'],
      author='Alvaro J. Iradier',
      url="http://www.trac-hacks.org/wiki/SearchAllPlugin",
      license='BSD',
      entry_points = {'trac.plugins': ['tracsearchall = tracsearchall']})
