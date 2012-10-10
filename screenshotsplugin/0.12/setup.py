#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard imports.
from setuptools import setup

# Trac imports.
from trac.util.dist import get_l10n_cmdclass

# Configure l18n message extractor.
extra = {}
cmdclass = get_l10n_cmdclass()
if cmdclass:
    extractors = [('**.py', 'python', None), ('**/templates/**.html', 'genshi',
      None)]
    extra['cmdclass'] = cmdclass
    extra['message_extractors'] = {'tracscreenshots' : extractors}

setup(
  name = 'TracScreenshots',
  version = '0.8',
  packages = ['tracscreenshots', 'tracscreenshots.db'],
  package_data = {'tracscreenshots' : ['templates/*.html', 'htdocs/css/*.css',
    'htdocs/js/*.js', 'locale/*/LC_MESSAGES/*.mo']},
  entry_points = {'trac.plugins': ['TracScreenshots.api = tracscreenshots.api',
    'TracScreenshots.core = tracscreenshots.core',
    'TracScreenshots.init = tracscreenshots.init',
    'TracScreenshots.matrix_view = tracscreenshots.matrix_view',
    'TracScreenshots.wiki = tracscreenshots.wiki',
    'TracScreenshots.timeline = tracscreenshots.timeline',
    'TracScreenshots.tags = tracscreenshots.tags [Tags]']},
  install_requires = ['Babel >= 0.9.4', 'Trac >= 0.12'],
  extras_require = {'Tags' : ['TracTags']},
  keywords = 'trac screenshots',
  author = 'Radek Bartoň',
  author_email = 'blackhex@post.cz',
  url = 'http://trac-hacks.org/wiki/ScreenshotsPlugin',
  description = 'Project screenshots plugin for Trac',
  license = '''GPL''',
  **extra
)
