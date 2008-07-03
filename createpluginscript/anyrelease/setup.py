from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='create_trac_plugin',
      version=version,
      description="utility to create the skeleton for a trac plugin",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='trac plugin',
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://trac-hacks.org/wiki/k0s',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,      
      install_requires=[
          # -*- Extra requirements: -*-
        'trac',
        'TracPluginTemplate'
      ],
      dependency_links=[
        'http://trac-hacks.org/svn/tracplugintemplatescript/0.11#egg=TracPluginTemplate'
        ],
      entry_points="""
      [console_scripts]
      create-trac-plugin = create_trac_plugin.create_plugin:main
      create-trac-component = create_trac_plugin.create_component:main
      """,
      )
