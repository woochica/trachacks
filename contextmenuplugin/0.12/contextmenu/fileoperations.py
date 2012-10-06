# -*- coding: utf-8 -*-
#
# Copyright (c) 2010, Logica
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

# This will become the TracSubversionWriteOperationsPlugin...

from genshi.builder import tag
from trac.core import Component, implements
from trac.util.translation import _

from api import ISourceBrowserContextMenuProvider

class DeleteResourceLink(Component):
    """Generate "Delete" menu item"""      
    implements(ISourceBrowserContextMenuProvider)
    # IContextMenuProvider methods
    def get_order(self, req):
        return 5

    def get_draw_separator(self, req):
        return False
    
    def get_content(self, req, entry, stream, data):
        href = req.href.browser(data['reponame'], entry.path, 
                                rev=data['stickyrev'], delete=1)
        return tag.a(_('Delete item'), href=href)


class CreateSubFolderLink(Component):
    """Generate "Create subfolder" menu item"""
    implements(ISourceBrowserContextMenuProvider)
    def get_order(self, req):
        return 15

    def get_draw_separator(self, req):
        return False
    
    # IContextMenuProvider methods
    def get_content(self, req, entry, stream, data):
        if entry.isdir:
            return tag.a(_('Create Subfolder'), href=req.href.newfolder(entry.path) + 'FIXME')
