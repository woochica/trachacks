from setuptools import setup

PACKAGE = 'TracPublishRevert'
VERSION = '0.2'

setup(name=PACKAGE,
      version=VERSION,
      packages=['publishrevert'],
      package_data={'publishrevert' : ['templates/*.cs']},
      entry_points={'trac.plugins': '%s = publishrevert' % PACKAGE},
)
