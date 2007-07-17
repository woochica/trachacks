from setuptools import setup

PACKAGE = 'ManualTestingPlugin'
VERSION = '0.0.1'

setup(
  name=PACKAGE,
  version=VERSION,
  packages=[PACKAGE],
  package_data={PACKAGE : [
    'htdocs/templates/*.cs',
    'htdocs/scripts/*.js',
    'htdocs/css/*.css'
  ]},
  entry_points={'trac.plugins': '%s = %s' % (PACKAGE, PACKAGE)},
  
  description='Plugin to make Trac support manual testing',
  keywords='trac plugin manual testing testcase testplan testsuite',  
  url='http://www.trac-hacks.org/wiki/ManualTestingPlugin',
  license='None yet',
  author='Ron Adams',
  author_email='eclip5e@visual-assault.org',
  long_description="""
    This Trac 0.10 plugin provides support for manual testing.

    See http://trac-hacks.org/wiki/ManualTestingPlugin for details.
  """,  
)