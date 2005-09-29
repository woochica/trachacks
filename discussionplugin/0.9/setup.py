from setuptools import setup

PACKAGE = 'TracDiscussion'
VERSION = '0.1'

setup(name=PACKAGE, version=VERSION, packages=['discussion'],
    package_data={'discussion' : ['templates/*.cs', 'htdocs/css/*.css']})
