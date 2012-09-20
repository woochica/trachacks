#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

version = '0.6.0'

setup(name='TracHoursPlugin',
      version=version,
      description="Trac the estimated and actual hours spent on tickets",
      author="David Turner and Jeff Hammel",
      author_email="jhammel@openplans.org",
      maintainer="Ryan J Ollos",
      maintainer_email="ryan.j.ollos@gmail.com",
      url="http://trac-hacks.org/wiki/TracHoursPlugin",
      keywords='trac plugin',
      license="GPL",
      packages=find_packages(exclude=['*.tests']),
      include_package_data=True,
      package_data={'trachours': ['templates/*']},
      zip_safe=False,
      install_requires=['Trac >= 0.12',
                        'python-dateutil',
                        'FeedParser',
                        'ComponentDependencyPlugin',
                        'TicketSidebarProvider',
                        'TracSQLHelper'],
      dependency_links=[
              "http://trac-hacks.org/svn/componentdependencyplugin/0.11#egg=ComponentDependencyPlugin",
              "http://trac-hacks.org/svn/ticketsidebarproviderplugin/0.11#egg=TicketSidebarProvider",
              "http://trac-hacks.org/svn/tracsqlhelperscript/0.12#egg=TracSQLHelper",
              ],
      extras_require=dict(lxml=['lxml']),
      entry_points="""
          [trac.plugins]
          trachours.trachours = trachours.hours
          trachours.multiproject = trachours.multiproject
          trachours.setup = trachours.setup
          trachours.ticket = trachours.ticket
          trachours.web_ui = trachours.web_ui
      """,
      test_suite='trachours.tests.test_suite',
      tests_require=[]
      )

