from setuptools import setup, find_packages
import sys, os

version = '0.7.1'

setup(name='TracLegos',
      version=version,
      description="front end to piecing together trac projects from configuration",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='trac',
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://www.openplans.org/people/k0s',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
        'Trac',
        'Genshi',
        'Paste',
        'PasteScript',
        'WebOb',
        'martINI',
      ],
      dependency_links=[
        'https://svn.openplans.org/svn/standalone/martINI#egg=martINI',
        ],
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      create-trac-project = traclegos.legos:main

      [paste.app_factory]
      main = traclegos.wsgiapp:make_app

      [paste.paster_create_template]
      trac_project = traclegos.pastescript.template:TracProjectTemplate

      [traclegos.database]
      SQLite = traclegos.db:SQLite
      MySQL = traclegos.db:MySQL
      PostgreSQL = traclegos.db:PostgreSQL

      [traclegos.respository]
      None = traclegos.repository:NoRepository
      ExistingSVNRepository = traclegos.repository:ExistingSVN
      NewSVNRepository = traclegos.repository:NewSVN
      SyncSVNRepository = traclegos.repository:SVNSync
      """,
      )
