from setuptools import setup

PACKAGE = 'tracsuperuser'
VERSION = '0.2'

setup(name=PACKAGE,
      version=VERSION,
      packages=['tracsuperuser'],
      author='Alvaro J. Iradier (AMB Sistemas)',
      url="http://www.trac-hacks.org/wiki/SuperUserPlugin",
      license='BSD',
      entry_points = {'trac.plugins': ['tracsuperuser = tracsuperuser']})
