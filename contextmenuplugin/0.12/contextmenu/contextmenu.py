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
'''
Created on 17 Jun 2010

@author: penmark
'''
from genshi.builder import tag
from trac.core import Component, ExtensionPoint, implements
from trac.web.api import ITemplateStreamFilter
from api import ISourceBrowserContextMenuProvider
from genshi.filters.transform import Transformer
from genshi.core import Markup
from trac.config import Option
from trac.versioncontrol.api import RepositoryManager
from trac.web.chrome import add_stylesheet, ITemplateProvider, add_javascript
from trac.util.translation import _
import os


class InternalNameHolder(Component):
    """ This component holds a reference to the file on this row
    for the javascript to use"""
    implements(ISourceBrowserContextMenuProvider)
    # IContextMenuProvider methods
    def get_order(self, req):
        return 0

    def get_draw_separator(self, req):
        return False
    
    def get_content(self, req, entry, stream, data):
        reponame = data['reponame'] or ''
        filename = os.path.normpath(os.path.join(reponame, entry.path))
        return tag.span(filename, class_="filenameholder %s" % entry.kind,
                        style="display:none")
    
class SubversionLink(Component):
    """Generate direct link to file in svn repo"""
    implements(ISourceBrowserContextMenuProvider)

    # IContextMenuProvider methods
    def get_order(self, req):
        return 1

    def get_draw_separator(self, req):
        return True
    
    def get_content(self, req, entry, stream, data):
        if self.env.is_component_enabled("svnurls.svnurls.svnurls"):
            # They are already providing links to subversion, so we won't duplicate them.
            return None
        if isinstance(entry, basestring):
            path = entry
        else:
            try:
                path = entry.path
            except AttributeError:
                path = entry['path']
        repos = RepositoryManager(self.env).get_repository(data['reponame'])
        return tag.a(_('Subversion'), href=repos.get_path_url(path, None))

class WikiToBrowserLink(Component):
    """Generate wiki link"""
    implements(ISourceBrowserContextMenuProvider)

    # IContextMenuProvider methods
    def get_order(self, req):
        return 2

    def get_draw_separator(self, req):
        return True
    
    def get_content(self, req, entry, stream, data):
        if isinstance(entry, basestring):
            path = entry
        else:
            try:
                path = entry.path
            except AttributeError:
                path = entry['path']
        href = ''
        if data['reponame']:
            href += '/' + data['reponame']
        href += '/' + path
        if data.has_key('rev'):
            href += "@%s" % data['rev']
        return tag.a(_('Wiki Link (to copy)'), href="source:%s" % href)

class SendResourceLink(Component):
    """Generate "Share file" menu item"""
    implements(ISourceBrowserContextMenuProvider)
    def get_order(self, req):
        return 10

    def get_draw_separator(self, req):
        return False
    
    # IContextMenuProvider methods
    def get_content(self, req, entry, stream, data):
        if not entry.isdir:
            return tag.a(_('Share file'), href=req.href.share(entry.path) + 'FIXME')

  
class SourceBrowserContextMenu(Component):
    """Component for adding a context menu to each item in the trac browser
    file-list
    """
    implements(ITemplateStreamFilter, ITemplateProvider)
    
    context_menu_providers = ExtensionPoint(ISourceBrowserContextMenuProvider)
    
    # ITemplateStreamFilter methods
    
    def filter_stream(self, req, method, filename, stream, data):
        if filename in ('browser.html', 'dir_entries.html'):
            if 'path' not in data:
                # Probably an upstream error
                return stream
            # provide a link to the svn repository at the top of the Browse Source listing
            if self.env.is_component_enabled("contextmenu.contextmenu.SubversionLink"):
                content = SubversionLink(self.env).get_content(req, data['path'], stream, data)
                if content:
                    stream |= Transformer("//div[@id='content']/h1").after(content)
            # No dir entries; we're showing a file
            if not data['dir']:
                return stream
            # FIXME: The idx is only good for finding rows, not generating element ids.
            # Xhr rows are only using dir_entries.html, not browser.html.
            # The xhr-added rows' ids are added using js (see expand_dir.js)
            idx = 0
            add_stylesheet(req, 'contextmenu/contextmenu.css')
            add_javascript(req, 'contextmenu/contextmenu.js')
            if 'up' in data['chrome']['links']:
                # Start appending stuff on 2nd tbody row when we have a parent dir link
                row_index = 2
                # Remove colspan and insert an empty cell for checkbox column
                stream |= Transformer('//table[@id="dirlist"]//td[@colspan="5"]').attr('colspan', None).before(tag.td())
            else:
                # First row = //tr[1]
                row_index = 1
            for entry in data['dir']['entries']:
                menu = tag.div(tag.span(Markup('&#9662;'),style="color: #bbb"),
                               tag.div(class_="ctx-foldable", style="display:none"),
                               id="ctx%s" % idx, class_="context-menu")
                for provider in sorted(self.context_menu_providers, key=lambda x: x.get_order(req)):
                    content = provider.get_content(req, entry, stream, data)
                    if content:
                        menu.children[1].append(tag.div(content))
                ## XHR rows don't have a tbody in the stream
                if data['xhr']:
                    path_prefix = ''
                else:
                    path_prefix = '//table[@id="dirlist"]//tbody'
                # Add the menu
                stream |= Transformer('%s//tr[%d]//td[@class="name"]' % (path_prefix, idx + row_index)).prepend(menu)
                if provider.get_draw_separator(req):
                    menu.children[1].append(tag.div(class_="separator"))
                # Add td+checkbox
                cb = tag.td(tag.input(type='checkbox', id="cb%s" % idx, class_='fileselect'))
                stream |= Transformer('%s//tr[%d]//td[@class="name"]' % (path_prefix, idx + row_index)).before(cb)
                idx += 1
            stream |= Transformer('//th[1]').before(tag.th())
        return stream
    
    # ITemplateProvider methods
    
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('contextmenu', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
