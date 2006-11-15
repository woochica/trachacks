from setuptools import setup

PACKAGE = 'tractab'
VERSION = '0.1.3'

setup(name=PACKAGE,
      version=VERSION,
      packages=[PACKAGE],
      package_data={PACKAGE : ['templates/*.cs']},
      entry_points={'trac.plugins': '%s = %s' % (PACKAGE, PACKAGE)},
)

