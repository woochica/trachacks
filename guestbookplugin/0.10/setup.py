#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
  name = 'TracGuestbook',
  version = '0.2',
  packages = ['guestbook', 'guestbook.db'],
  package_data = {'guestbook': ['templates/*.cs', 'htdocs/css/*.css']},
  entry_points = {'trac.plugins': ['TracGuestbook.core = guestbook.core',
                                   'TracGuestbook.init = guestbook.init']},
  keywords = 'trac guestbook',
  author = 'Radek Bartoň',
  author_email = 'blackhex@post.cz',
  url = 'http://trac-hacks.swapoff.org/wiki/GuestbookPlugin',
  description = 'Guestbook plugin for Trac',
  license = '''GPL'''
)
