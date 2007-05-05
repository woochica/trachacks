from setuptools import setup

PACKAGE = 'AztechCalendar'
VERSION = '0.1'

setup(name=PACKAGE, version=VERSION, 
	packages=['azcalendar'],
	package_data={'azcalendar': ['templates/*.cs', 'htdocs/images/*.jpg', 'htdocs/css/*.css','templates/*.cs']})
