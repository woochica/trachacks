from setuptools import setup

PACKAGE = 'TracDrupalIntegration'
VERSION = '0.1'

setup(name=PACKAGE,
	version=VERSION,
	packages=['drupalintegration'],
	entry_points={'trac.plugins': '%s = drupalintegration' % PACKAGE},
	maintainer='Andrew Steinborn',
	maintainer_email='tuxlover684 -at- gmail -dot- com',
	url='http://trac-hacks.org/wiki/DrupalIntegration',
)
