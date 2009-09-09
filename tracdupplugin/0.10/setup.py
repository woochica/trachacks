# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

from setuptools import find_packages, setup

setup(
  name='TracDupPlugin',
  version=0.1.1,
  description='duplication of tickets to other tickets',
  long_description=""" """,
  classifiers=[
    'Framework :: Trac',
    'License :: OSI Approved :: BSD License', 
  ],
  keywords='trac.ticket',
  author='Thomas Vander Stichele',
  author_email='thomas (at) apestaart (dot) org',
  url='http://trac-hacks.org/wiki/TracDupPlugin',
  license='BSD',
  packages=find_packages(exclude=['*.tests*']),
  entry_points = """
    [trac.plugins]
    tracdup = tracdup.ticket
  """,
  test_suite="tracdup.tests",
)
