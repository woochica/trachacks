from setuptools import setup

PACKAGE = 'FlashView'
VERSION = '0.1.3'

setup(name=PACKAGE,
      version=VERSION,
      packages=['flashview'],
      author = 'Yuanying',
      author_email = 'yuanying@fraction.jp',
      url = 'http://trac-hacks.org/wiki/FlashViewPlugin',
      description = 'Flash view plugin for Trac',
      license='BSD',
      entry_points={'trac.plugins': '%s = flashview' % PACKAGE},
)
