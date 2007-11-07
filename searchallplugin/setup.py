from setuptools import setup

PACKAGE = 'tracsearchall'
VERSION = '0.1'

setup(name='tracsearchall',
      version='0.1',
      packages=['tracsearchall'],
      author='Alvaro J. Iradier',
      url="http://www.trac-hacks.org/wiki/SearchAllPlugin",
      license='BSD',
      entry_points = {'trac.plugins': ['tracsearchall = tracsearchall']})
