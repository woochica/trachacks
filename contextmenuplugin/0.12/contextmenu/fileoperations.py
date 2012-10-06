# coding: utf-8
#
# Copyright (c) 2010, Logica
# 
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
#     * Redistributions of source code must retain the above copyright 
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither Logica nor the names of its contributors may be used to 
#       endorse or promote products derived from this software without 
#       specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------


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
