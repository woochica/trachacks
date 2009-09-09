# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

from setuptools import find_packages, setup

setup(
  name='TracDupPlugin',
  version=0.1.1,
  packages=find_packages(exclude=['*.tests*']),
  entry_points = """
    [trac.plugins]
    tracdup = tracdup.ticket
  """,
  test_suite="tracdup.tests",
)
