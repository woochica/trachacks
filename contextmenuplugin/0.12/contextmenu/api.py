# -*- coding: utf-8 -*-
#
# Copyright (c) 2010, Logica
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.core import Interface

class ISourceBrowserContextMenuProvider(Interface):
    def get_order(req):
        """Return preferred sort position (integer, 0 is top)"""

    def get_draw_separator(req):
        """Whether a separator should be rendered after this provider (boolean)"""
        
    def get_content(req, item, stream, data):
        """Return genshi tag, or None to skip this menu item."""
