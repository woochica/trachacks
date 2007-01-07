from setuptools import setup

PACKAGE = 'TracBurndown'
VERSION = '01.05.10' # the last two decimals are meant to signify the Trac version

setup(name=PACKAGE,
      description='Plugin to provide a dynamic burndown chart in Trac.',
      keywords='trac plugin scrum burndown',
      url='http://www.trac-hacks.org/wiki/ScrumBurndownPlugin',
      version=VERSION,
      packages=['burndown'],
      package_data={'burndown' : ['htdocs/js/*.js', 'htdocs/css/*.css', 'htdocs/images/*.jpg' ,'templates/*.cs']},
      entry_points={'trac.plugins': '%s = burndown' % PACKAGE},
)