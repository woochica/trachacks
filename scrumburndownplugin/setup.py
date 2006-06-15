from setuptools import setup

PACKAGE = 'TracBurndown'
VERSION = '0.1'

setup(name=PACKAGE,
      version=VERSION,
      packages=['burndown'],
      package_data={'burndown' : ['htdocs/js/*.js', 'htdocs/css/*.css', 'htdocs/images/*.jpg' ,'templates/*.cs']},
      entry_points={'trac.plugins': '%s = burndown' % PACKAGE},
)