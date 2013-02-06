#!/usr/bin/python

from setuptools import find_packages, setup

setup(
    name='tracticketweightPlugin',
    version='0.1.1',
    keywords='trac plugin ticket weight',
    author='Zack Shahan',
    author_email='zshahan@dig-inc.net',
    url='null',
    description='Trac Ticket Weight Plugin',
    long_description="""

""",
    license='BSD',

    install_requires=['Trac >= 0.12dev'],

    packages=['tracticketweight'],

    entry_points={
        'trac.plugins': [
            'tracticketweight.api = tracticketweight.api',
        ],
    },
)
