from setuptools import setup

PACKAGE = 'AuthForm'
VERSION = '0.1'

setup(name=PACKAGE, version=VERSION, packages=['authform'],
        package_data={'authform' : ['templates/*.cs',]})
