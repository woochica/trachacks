from setuptools import setup

PACKAGE = 'FlashView'
VERSION = '0.1.3'

setup(name=PACKAGE,
      version=VERSION,
      packages=['flashview'],
      entry_points={'trac.plugins': '%s = flashview' % PACKAGE},
)