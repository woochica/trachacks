#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name='WikifyAnythingPlugin',
    version='0.2',
    packages=find_packages(exclude=['*.tests*']),
    author='Todd Radel',
    author_email = 'todd.radel@eds.com',
    description='Allows you to "wikify" any text on any template within Trac.',
    url='http://ba7development/trac/WikifyAnythingPlugin',
    license='GPL',
    entry_points = {
        'trac.plugins': [
            'WikifyAnything = wikify.plugin',
        ]
    },
    package_data = {
    }
)
