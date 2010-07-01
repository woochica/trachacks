#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 et
# ==============================================================================
# Copyright © 2008 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# ==============================================================================

import re
from setuptools import setup
import tracext.google.analytics as tg

setup(
    name = tg.__package__,
    version = tg.__version__,
    author = tg.__author__,
    author_email = tg.__email__,
    description = tg.__summary__,
    license = tg.__license__,
    url = tg.__url__,
    download_url = 'http://python.org/pypi/%s' % tg.__package__,
    long_description = re.sub(r'(\.\.[\s]*[\w]*::[\s]*[\w+]*\n)+', r'::\n',
                              open('README.txt').read()),
    packages = ['googleanalytics'],
    package_data = {'googleanalytics': ['templates/*.html',
                                                 'htdocs/*.css']},
    include_package_data = True,
    install_requires = ['Trac>=0.11'],
    keywords = "trac plugin google analytics",
    entry_points = """
    [trac.plugins]
      googleanalytics = tracext.google.analytics
      googleanalytics.admin = googleanalytics.admin
      googleanalytics.web_ui = googleanalytics.web_ui
    """,
    classifiers = ['Framework :: Trac']
)
