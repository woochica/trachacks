from setuptools import setup

PACKAGE = 'tracsuperuser'
VERSION = '0.3'

setup(name=PACKAGE,
    version=VERSION,
    packages=['tracsuperuser'],
    author='Alvaro J. Iradier',
    author_email = "alvaro.iradier@polartech.es",
    description = "Create a super user that always has TRAC_ADMIN permissions",
    long_description = "",
    license = "GPL",
    keywords = "trac plugin auth superuser admin",
    
    url="http://www.trac-hacks.org/wiki/SuperUserPlugin",
    
    entry_points = {'trac.plugins': ['tracsuperuser = tracsuperuser']})
