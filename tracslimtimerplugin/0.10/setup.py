
from setuptools import setup

PACKAGE = 'TracSlimTimer'
VERSION = '0.1.0'

setup(
    name=PACKAGE,
    version=VERSION,

    packages=['tracslimtimer'],
    package_data = {'tracslimtimer': ['templates/*',
	'htdocs/css/*.css',
	'htdocs/js/*.js'
	]},
    install_requires = ['elementtree>=1.2.6-20050316','MySQL-python>=1.2.2'],
    entry_points = {
        'trac.plugins': 'tracslimtimer = tracslimtimer'
    },

    description='SlimTimer integration for Trac',
    keywords='trac slimtimer slim timer',
    license = 'BSD',
    url = 'http://www.trac-hacks.org/wiki/TracSlimTimerPlugin',
    author='Brian Birtles',
    author_email='birtles@gmail.com',
    long_description="""
    Provides some basic integration of trac and SlimTimer as well as more
    general utilities for extracting data from SlimTimer.
    """,
    zip_safe=True
)

