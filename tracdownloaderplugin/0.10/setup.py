#!/usr/bin/env python
# -*- coding: utf8 -*-
import ez_setup
ez_setup.use_setuptools()

from setuptools import setup

setup(
  name = 'TracDownloader',
  version = '0.1',
  packages = ['downloader'],
  package_data = {'downloader' : ['templates/*.cs', 
                                  'htdocs/css/*.css',
                                  'htdocs/img/*.png',
                                  '*.txt']},
  entry_points = {'trac.plugins': ['downloader.web_ui = downloader.web_ui',
                                   'downloader.admin = downloader.admin',
                                   'downloader.db = downloader.db',
                                   'downloader.model = downloader.model']
                  },
  install_requires = ['PyCAPTCHA >= 0.4',
                      'PIL >= 1.1.5'],
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
