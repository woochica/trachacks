#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#
# Copyright 2007-2008 Optaros, Inc
#

from setuptools import setup

setup(name="TracSectionEditPlugin",
      version="0.2.3",
      packages=['tracsectionedit'],
      author="Catalin Balan", 
      author_email="cbalan@optaros.com", 
      url="http://code.optaros.com/trac/oforge",
      description="Trac Section Edit based on http://trac.edgewall.org/ticket/6921",
      license="BSD",
      entry_points={'trac.plugins': [
            'tracsectionedit.web_ui = tracsectionedit.web_ui', 
            ]},
      package_data={'tracsectionedit' : ['htdocs/js/*.js']}
)
