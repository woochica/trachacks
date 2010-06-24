# -*- coding: iso-8859-1 -*-
#
# Copyright (C) 2004-2006 Edgewall Software
# Copyright (C) 2009 Piers O'Hanlon
# Copyright (C) 2009 David Fraser
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.
#
# For trac 0.9.3
# To enable this extension you need to add 
#                      'trac.mimeview.wikicreole', 
# to the following file - to the default_components variable:
#../db_default.py:440
# default_components = ('trac.About', 'trac.attachment', 
#
# Trac 0.11
# This package should now install using easy_setup
# 
# If you don't use setuptools then Add to the following to:
# /usr/lib/python2.5/site-packages/Trac-0.11.egg-info/entry_points.txt, SOURCES.txt
#	trac.mimeview.wikicreole = trac.mimeview.wikicreole
#
# Author: David Fraser <davidf@sjsoft.com>
# Adapted from ManPageRendererPlugin by Piers O'Hanlon <p.ohanlon@cs.ucl.ac.uk>

"""Trac support for wiki creole pages
See wikicreole for more info: http://www.wikicreole.org/
"""

from trac.core import *
from trac.mimeview.api import IHTMLPreviewRenderer, content_to_unicode
import creoleparser

class WikiCreoleRenderer(Component):
    """Renders WikiCreole text as HTML."""
    implements(IHTMLPreviewRenderer)

    expand_tabs = False

    def get_quality_ratio(self, mimetype):
        if mimetype in ['text/x-wiki.creole']:
            return 9
        return 0

    def render(self, req, mimetype, content, filename=None, rev=None):
        """Returns wikicreole text as html"""
        text = content_to_unicode(self.env, content, mimetype)
        if text.startswith(u"\ufeff"):
            text = text[1:]
        html = creoleparser.creole2html(text)
        return html

