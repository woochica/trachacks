#!/usr/bin/env python

from setuptools import find_packages, setup

PACKAGE='sslauthentication'
VERSION='0.1'

setup(
    name=PACKAGE,
    version=VERSION,
    packages=find_packages(exclude=['*.tests*']),
    author="Giel van Schijndel",
    author_email="me@mortis.eu",
    description="This plugin allows authentication of users by making use of SSL client certificates.",
    license="GPL",
    url="http://www.mortis.eu/",
    entry_points = """
        [trac.plugins]
        sslauthentication = sslauthentication
    """
)
