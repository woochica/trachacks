from setuptools import setup, find_packages

PACKAGE = 'TracBurndown'
VERSION = '1.9'

setup(name=PACKAGE,
      description='Plugin to provide a dynamic burndown chart in Trac.',
      keywords='trac plugin scrum burndown',
      url='http://www.trac-hacks.org/wiki/ScrumBurndownPlugin',
      version=VERSION,
      packages=find_packages(exclude=['ez_setup']),
      package_data={'burndown' : ['htdocs/js/*.js', 'htdocs/css/*.css', 'htdocs/images/*' ,'templates/*']},
      entry_points={'trac.plugins': '%s = burndown' % PACKAGE},
      tests_require=['nose'],
      test_suite = 'nose.collector'
)
