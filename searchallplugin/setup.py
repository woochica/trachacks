from setuptools import setup

PACKAGE = 'tracsearchall'
VERSION = '0.7'

setup(name=PACKAGE,
    version=VERSION,
    packages=['tracsearchall'],
    author='Alvaro J. Iradier',
    author_email = "alvaro.iradier@polartech.es",
    description = "Search in all projects in the same parent folder",
    long_description = "",
    url="http://www.trac-hacks.org/wiki/SearchAllPlugin",
    license='GPL',
    entry_points = {'trac.plugins': ['tracsearchall = tracsearchall']})
