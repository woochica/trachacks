from setuptools import setup

PACKAGE = 'Gullible Authentication'
VERSION = '0.1'

setup(name=PACKAGE,
      version=VERSION,
      packages=['gullible'],
      entry_points={'trac.plugins': '%s = gullible' % PACKAGE},
)



