#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
  name = 'TracDiscussion',
  version = '0.8',
  packages = ['tracdiscussion', 'tracdiscussion.db'],
  package_data = {'tracdiscussion' : ['templates/*.html', 'templates/*.txt',
    'templates/*.rss', 'htdocs/css/*.css', 'htdocs/js/*.js', 'htdocs/*.png']},
  entry_points = {'trac.plugins': ['TracDiscussion.ajax = tracdiscussion.ajax',
    'TracDiscussion.api = tracdiscussion.api',
    'TracDiscussion.core = tracdiscussion.core',
    'TracDiscussion.init = tracdiscussion.init',
    'TracDiscussion.wiki = tracdiscussion.wiki',
    'TracDiscussion.timeline = tracdiscussion.timeline',
    'TracDiscussion.admin = tracdiscussion.admin',
    'TracDiscussion.search = tracdiscussion.search',
    'TracDiscussion.notification = tracdiscussion.notification',
    'TracDiscussion.spamfilter = tracdiscussion.spamfilter [SpamFilter]']},
  install_requires = ['Trac'],
  extras_require = {'SpamFilter' : ['TracSpamFilter']},
  keywords = 'trac discussion e-mail',
  author = 'Radek Bartoň',
  author_email = 'blackhex@post.cz',
  url = 'http://trac-hacks.org/wiki/DiscussionPlugin',
  description = 'Discussion forum plugin for Trac',
  license = '''GPL'''
)
