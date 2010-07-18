#!/usr/bin/python

from setuptools import setup

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

