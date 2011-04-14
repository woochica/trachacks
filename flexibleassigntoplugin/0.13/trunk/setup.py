#!/usr/bin/env python

from setuptools import find_packages, setup

from flexibleassignto import flexibleassignto
VERSION = flexibleassignto.version

PACKAGE = 'FlexibleAssignTo'

setup(
    name = PACKAGE,
    version = VERSION,
    description = "A Trac extension point for customizing the Assign To ticket field.",
    author = "Robert Morris",
    author_email = "gt4329b@pobox.com",
    license='BSD',
    url='',
    keywords='',
    packages=find_packages(exclude=['ez_setup','*.tests*']),
    package_data={},
    entry_points = \
"""[trac.plugins]
flexibleassignto = flexibleassignto
""",
)

classifiers = [
  'Development Status :: 3 - Alpha',
  'Environment :: Plugins',
  'Framework :: Trac',
  'Intended Audience :: Developers',
  'Intended Audience :: System Administrators',
  'Natural Language :: English',
  'Programming Language :: Python'
]
