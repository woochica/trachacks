from setuptools import setup

PACKAGE = 'restrictownertolist'
VERSION = '0.1.0'

setup(name=PACKAGE,
    version=VERSION,
    packages=['restrictownertolist'],
    package_data={
        'restrictownertolist': []
    },
    author='Alvaro J. Iradier',
    author_email = "alvaro.iradier@polartech.es",
    description = "Restrict owners of a ticket to a specified list",
    long_description = "",
    license = "GPL",
    keywords = "trac plugin owner ticket", 
    url="",
    
    entry_points = {
        'trac.plugins': ['restrictownertolist = restrictownertolist']
    })
