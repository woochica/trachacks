from setuptools import setup

PACKAGE = 'ManualTesting'
VERSION = '0.0.1'

setup(
  name = PACKAGE,
  version = VERSION,
  packages = ['manualtesting'],
  package_data = {
      'manualtesting' : [
        'htdocs/templates/*.cs',
        'htdocs/scripts/*.js',
        'htdocs/css/*.css'
      ]
  },
  entry_points = {
      'trac.plugins': [
          '%s.core = manualtesting.core' % PACKAGE,
          '%s.UICore = manualtesting.UICore' % PACKAGE,
          '%s.MTP_EnvironmentSetupParticipant = manualtesting.MTP_EnvironmentSetupParticipant' % PACKAGE,
          '%s.MTP_NavigationContributor = manualtesting.MTP_NavigationContributor' % PACKAGE,
          '%s.MTP_TemplateProvider = manualtesting.MTP_TemplateProvider' % PACKAGE,
          '%s.MTP_RequestHandler = manualtesting.MTP_RequestHandler' % PACKAGE
      ]
  },
  description = 'Plugin to make Trac support manual testing',
  keywords = 'trac plugin manual testing testcase testplan testsuite',
  url = 'http://www.trac-hacks.org/wiki/ManualTestingPlugin',
  license = 'None yet',
  author = 'Ron Adams',
  author_email = 'eclip5e@visual-assault.org',
  long_description =
  """
    This Trac 0.10 plugin provides support for manual testing.

    See http://trac-hacks.org/wiki/ManualTestingPlugin for details.
  """
)