from setuptools import setup

PACKAGE = 'TracTab'
VERSION = '0.1.4'

setup(name=PACKAGE,
      version=VERSION,
      packages=[PACKAGE],
      package_data={PACKAGE : ['templates/*.html']},
      entry_points={'trac.plugins': '%s = %s' % (PACKAGE, PACKAGE)},
)

