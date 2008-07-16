from setuptools import setup

PACKAGE = 'tracsuperuser'
VERSION = '0.2'

setup(name='tracsuperuser',
      version='0.1',
      packages=['tracsuperuser'],
      author='Alvaro J. Iradier (AMB Sistemas)',
      url="http://www.trac-hacks.org/wiki/SuperUserPlugin",
      license='BSD',
      entry_points = {'trac.plugins': ['tracsuperuser = tracsuperuser']})
