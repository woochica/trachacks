from setuptools import setup

PACKAGE = 'TracBurndown'
VERSION = '01.01.10' # the last two decimals are meant to signify the Trac version

setup(name=PACKAGE,
      description='Plugin to provide a dynamic burndown chart in Trac.',
      keywords='trac plugin burndown',
      version=VERSION,
      packages=['burndown'],
      package_data={'burndown' : ['htdocs/swf/*.swf', 'htdocs/css/*.css', 'templates/*.cs']},
      entry_points={'trac.plugins': '%s = burndown' % PACKAGE},
)