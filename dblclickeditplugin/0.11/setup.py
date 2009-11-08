#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#
# Copyright 2009 Yijun Yu

from setuptools import setup

setup(name="DblClickEditPlugin",
      version="0.1",
      packages=['dblclickedit'],
      author="Yijun Yu", 
      author_email="y.yu@open.ac.uk", 
      url="http://mcs.open.ac.uk/yy66",
      description="Edit a page by double clicking at it.",
      license="BSD",
      entry_points={'trac.plugins': [
            'dblclickedit.web_ui = dblclickedit.web_ui', 
            ]},
      package_data={'dblclickedit' : ['htdocs/js/*.js']}
)
