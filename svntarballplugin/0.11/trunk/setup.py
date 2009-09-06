from setuptools import setup

PACKAGE = 'TracSVNTarBall'
VERSION = '0.1'

setup(name=PACKAGE,
      version=VERSION,
      packages=['svntarball'],
      entry_points={'trac.plugins': '%s = svntarball' % PACKAGE},
)
