from setuptools import setup

PACKAGE = 'TracGeneralLink'
VERSION = '0.1'

setup(name=PACKAGE, version=VERSION, packages=['GeneralLinkSyntax'],
      package_data={'GeneralLinkSyntax': ['templates/*.cs', 'htdocs/css/*.css']})
