from setuptools import setup

PACKAGE = 'tractab'
VERSION = '0.1.3'

setup(name=PACKAGE,
      version=VERSION,
      license='BSD',
      author='Bobby Smith',
      author_email='bobbysmith007@gmail.com',
      maintainer='Ryan J Ollos',
      maintainer_email='ryan.j.ollos.@gmail.com',      
      packages=[PACKAGE],
      package_data={PACKAGE : ['templates/*.cs']},
      entry_points={'trac.plugins': '%s = %s' % (PACKAGE, PACKAGE)},
)

