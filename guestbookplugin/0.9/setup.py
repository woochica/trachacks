#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
  name='TracGuestbook',
  version='0.1',
  author='Radek Bartoň',
  author_email='blackhex@post.cz',
  description='Guestbook plugin for Trac',
  long_description='',
  url='http://trac-hacks.swapoff.org/wiki/GuestbookPlugin',
  keywords='trac guestbook',
  packages=['guestbook'],
  package_data={'guestbook': ['templates/*.cs', 'htdocs/css/*.css']},
  entry_points={'trac.plugins': 'TracGuestbook = guestbook.core'})
