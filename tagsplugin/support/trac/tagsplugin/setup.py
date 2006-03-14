from setuptools import setup

setup(
    name='TracTags',
    version='0.2',
    packages=['tractags'],
	package_data={'tractags' : ['templates/*.cs', 'htdocs/js/*.js', 'htdocs/css/*.css']},
    author='Muness Alrubaie',
    url='http://dev.muness.textdriven.com/trac.cgi/wiki/tags',
    description='Tag plugin for Trac',
    )
