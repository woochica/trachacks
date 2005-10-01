from setuptools import setup

PACKAGE = 'TracTags'
VERSION = '0.1'

setup(name=PACKAGE, version=VERSION, packages=['tractags'],
	package_data={'tractags' : ['templates/*.cs' ]})
