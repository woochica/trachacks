from setuptools import setup

PACKAGE = 'tractab'
VERSION = '0.1.3-Genshi'

setup(name=PACKAGE,
      version=VERSION,
      packages=[PACKAGE],
      package_data={PACKAGE : ['templates/*.html']},
      entry_points={'trac.plugins': '%s = %s' % (PACKAGE, PACKAGE)},
)

