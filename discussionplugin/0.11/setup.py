#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
import sys

min_python = (2, 5)
if sys.version_info < min_python:
    print "DiscussionPlugin requires Python %d.%d or later" % min_python
    sys.exit(1)
if sys.version_info >= (3,):
    print "DiscussionPlugin doesn't support Python 3 (yet)"
    sys.exit(1)

setup(
  name = 'TracDiscussion',
  version = '0.8',
  packages = ['tracdiscussion', 'tracdiscussion.db'],
  package_data = {'tracdiscussion' : ['templates/*.html', 'templates/*.txt',
    'templates/*.rss', 'htdocs/css/*.css', 'htdocs/js/*.js', 'htdocs/*.png']},
  entry_points = {'trac.plugins': ['TracDiscussion.admin = tracdiscussion.admin',
    'TracDiscussion.ajax = tracdiscussion.ajax',
    'TracDiscussion.api = tracdiscussion.api',
    'TracDiscussion.core = tracdiscussion.core',
    'TracDiscussion.init = tracdiscussion.init',
    'TracDiscussion.notification = tracdiscussion.notification',
    'TracDiscussion.search = tracdiscussion.search',
    'TracDiscussion.spamfilter = tracdiscussion.spamfilter [SpamFilter]',
    'TracDiscussion.tags = tracdiscussion.tags [Tags]',
    'TracDiscussion.timeline = tracdiscussion.timeline',
    'TracDiscussion.wiki = tracdiscussion.wiki']},
  install_requires = ['Trac'],
  extras_require = {'SpamFilter' : ['TracSpamFilter'],
                    'Tags' : ['TracTags']},
  keywords = 'trac discussion e-mail',
  author = 'Radek Bartoň',
  author_email = 'blackhex@post.cz',
  url = 'http://trac-hacks.org/wiki/DiscussionPlugin',
  description = 'Discussion forum plugin for Trac',
  license = '''GPL'''
)
