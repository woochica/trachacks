#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

themes = ['blue', 'default', 'dokuwiki', 'flower', 'i18n', 'pixel', 'yatil']

data = ['templates/*.html', 'htdocs/*.png'] + \
       ['htdocs/ui/%s/*.*' % theme for theme in themes]

setup(name='SlideShow',
      version='0.3',
      packages=['slideshow'],
      author='Alec Thomas',
      maintainer = 'Ryan J Ollos',
      maintainer_email = 'ryan.j.ollos@gmail.com',
      url='http://trac-hacks.org/wiki/SlideShowPlugin',
      license='Public Domain',
      zip_safe = False,
      install_requires = ['trac >= 0.11'], 
      entry_points = {'trac.plugins': ['slideshow = slideshow.slideshow']},
      package_data={'slideshow' : data}
      )
