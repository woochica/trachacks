#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ez_setup
ez_setup.use_setuptools()

from setuptools import setup

setup(
  name = 'TracDownloader',
  version = '0.1',
  packages = ['tracdownloader'],
  package_data = {'tracdownloader' : ['templates/*.cs', 
                                  'htdocs/css/*.css',
                                  'htdocs/img/*.png',
                                  '*.txt']},
  entry_points = {'trac.plugins': ['tracdownloader.web_ui = tracdownloader.web_ui',
                                   'tracdownloader.admin = tracdownloader.admin',
                                   'tracdownloader.db = tracdownloader.db',
                                   'tracdownloader.model = tracdownloader.model']
                  },
  """install_requires = ['PyCAPTCHA >= 0.4',
                      'PIL >= 1.1.5'],"""
  extras_require = {},
  keywords = 'trac downloader',
  author = 'Petr Škoda',
  author_email = 'pecast_cz@seznam.cz',
  url = 'http://trac-hacks.org/wiki/TracDownloaderPlugin',
  description = """
  Project release downloader plugin for Trac system with
  optional questionnaire before download of file, Captcha
  user check, stats module and easy to use admin.
  """,
  license = '''GPL''',
  zip_safe = False
) 
