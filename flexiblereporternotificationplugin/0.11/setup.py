from setuptools import setup

PACKAGE = 'flexiblereporternotification'

setup(name=PACKAGE,
      version='0.0.1',
      packages=[PACKAGE],
      url='http://trac-hacks.org/wiki/FlexibleReporterNotificationPlugin',
      author='Satyam'
      long_description="""
      
      """,
      entry_points={'trac.plugins': '%s = %s' % (PACKAGE, PACKAGE)},
)

