from setuptools import setup, find_packages
import sys, os

version = '0.2.1'

setup(name='TracSQLHelper',
      version=version,
      description="SQL Helper functions for Trac",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='SQL Trac',
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://trac-hacks.org/wiki/k0s',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
        'Trac',
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
