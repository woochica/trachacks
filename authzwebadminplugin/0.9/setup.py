from setuptools import setup

PACKAGE='TracWebAdminAuthz'
VERSION='0.2'

setup(name=PACKAGE, version=VERSION, packages=['webadmin_authz'],
	package_data={'webadmin_authz' : ['templates/*.cs']})
