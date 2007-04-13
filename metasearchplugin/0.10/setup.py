from setuptools import setup

PACKAGE = 'tracmetasearch'
VERSION = '0.3'

setup(name='tracmetasearch',
      version='0.3',
      packages=['tracmetasearch'],
      author='aamk - Martin Kutter',
      url="http://www.trac-hacks.org/wiki/MetaSearchPlugin",
      license='BSD',
      entry_points = {'trac.plugins': ['tracmetasearch = tracmetasearch']})
