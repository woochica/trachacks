#!/usr/bin/python

from setuptools import setup

# Tell setuptools to ignore my .svn directories
# http://stackoverflow.com/questions/1129180/how-can-i-make-setuptools-ignore-subversion-inventory
from setuptools.command import sdist
del sdist.finders[:]


setup(
    name='GitoriousPlugin',
    version='0.1',
    packages=['gitoriousplugin'],
    author='Aurelien Bompard',
    author_email='aurelien@bompard.org',
    description='A plugin to use Gitorious as the source code hosting provider',
    entry_points = """
[trac.plugins]
gitorious = gitoriousplugin
    """,
    install_requires = [ "Trac", ]
)

