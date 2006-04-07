from setuptools import setup

PACKAGE = 'TracCodeReview'
VERSION = '0.3'

setup(name=PACKAGE, version=VERSION, packages=['codereview'],
        package_data={'codereview' : ['templates/*.cs', 'htdocs/images/*.*']})
