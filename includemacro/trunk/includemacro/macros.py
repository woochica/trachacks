# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2008 Noah Kantrowitz <noah@coderanger.net>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import urllib2
from StringIO import StringIO

from genshi.core import escape
from genshi.filters.html import HTMLSanitizer
from genshi.input import HTMLParser, ParseError
from trac.core import *
from trac.mimeview.api import Mimeview, get_mimetype, Context
from trac.perm import IPermissionRequestor
from trac.resource import ResourceNotFound
from trac.ticket.model import Ticket
from trac.versioncontrol.api import RepositoryManager
from trac.wiki.formatter import system_message
from trac.wiki.macros import WikiMacroBase
from trac.wiki.model import WikiPage

__all__ = ['IncludeMacro']

class IncludeMacro(WikiMacroBase):
    """A macro to include other resources in wiki pages.
    More documentation to follow.
    """
    
    implements(IPermissionRequestor)
    
    # Default output formats for sources that need them
    default_formats = {
        'wiki': 'text/x-trac-wiki',
    }
    
    # IWikiMacroProvider methods
    def expand_macro(self, formatter, name, content):
        args = [x.strip() for x in content.split(',')]
        if len(args) == 1:
            args.append(None)
        elif len(args) != 2:
            return system_message('Invalid arguments "%s"'%content)
            
        # Pull out the arguments
        source, dest_format = args
        try:
            source_format, source_obj = source.split(':', 1)
        except ValueError: # If no : is present, assume its a wiki page
            source_format, source_obj = 'wiki', source
            
        # Apply a default format if needed
        if dest_format is None:
            try:
                dest_format = self.default_formats[source_format]
            except KeyError:
                pass
        
        if source_format in ('http', 'https', 'ftp'):
            # Since I can't really do recursion checking, and because this 
            # could be a source of abuse allow selectively blocking it.
            # RFE: Allow blacklist/whitelist patterns for URLS. <NPK>
            # RFE: Track page edits and prevent unauthorized users from ever entering a URL include. <NPK>
            if not formatter.perm.has_permission('INCLUDE_URL'):
                self.log.info('IncludeMacro: Blocking attempt by %s to include URL %s on page %s',
                              formatter.req.authname, source, formatter.req.path_info)
                return ''
            try:
                urlf = urllib2.urlopen(source)
                out = urlf.read()  
            except urllib2.URLError, e:
                return system_message('Error while retrieving file', str(e))
            except TracError, e:
                return system_message('Error while previewing', str(e))
            ctxt = Context.from_request(formatter.req)
        elif source_format == 'wiki':
            # XXX: Check for recursion in page includes. <NPK>
            if '@' in source_obj:
                page_name, page_version = source_obj.split('@', 1)
            else:
                page_name, page_version = source_obj, None
            page = WikiPage(self.env, page_name, page_version)
            if not 'WIKI_VIEW' in formatter.perm(page.resource):
                return ''
            if not page.exists:
                if page_version:
                    return system_message('No version "%s" for wiki page "%s"' % (page_version, page_name))
                else:
                    return system_message('Wiki page "%s" does not exist' % page_name)
            out = page.text
            ctxt = Context.from_request(formatter.req, 'wiki', source_obj)
        elif source_format == 'source':
            if not formatter.perm.has_permission('FILE_VIEW'):
                return ''
            out, ctxt, dest_format = self._get_source(formatter, source_obj, dest_format)
        elif source_format == 'ticket':
            if ':' in source_obj:
                ticket_num, source_obj = source_obj.split(':', 1)
                if not Ticket.id_is_valid(ticket_num):
                    return system_message("%s is not a valid ticket id" % ticket_num)
                try:
                    ticket = Ticket(self.env, ticket_num)
                    if not 'TICKET_VIEW' in formatter.perm(ticket.resource):
                        return ''
                except ResourceNotFound, e:
                    return system_message("Ticket %s does not exist" % ticket_num)
                if ':' in source_obj:
                    source_format, comment_num = source_obj.split(':', 1)
                    if source_format == 'comment':
                        changelog = ticket.get_changelog()
                        out = []
                        if changelog:
                            for (ts, author, field, oldval, newval, permanent) in changelog:
                                if field == 'comment' and oldval == comment_num:
                                    dest_format = 'text/x-trac-wiki'
                                    ctxt = Context.from_request(formatter.req, 'ticket', ticket_num)
                                    out = newval
                                    break
                        if not out:
                            return system_message("Comment %s does not exist for Ticket %s" % (comment_num, ticket_num))
                    else:
                        system_message("Unsupported ticket field %s" % source_format)
            else:
                return system_message('Ticket field must be specified')
        else:
            # RFE: Add ticket: and comment: sources. <NPK>
            # RFE: Add attachment: source. <NPK>
            return system_message('Unsupported realm %s' % source)
        
        # If we have a preview format, use it
        if dest_format:
            out = Mimeview(self.env).render(ctxt, dest_format, out)
        
        # Escape if needed
        if not self.config.getbool('wiki', 'render_unsafe_content', False):
            try:
                out = HTMLParser(StringIO(out)).parse() | HTMLSanitizer()
            except ParseError:
                out = escape(out)
        
        return out
            
    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'INCLUDE_URL'
    
    # Private methods
    def _get_source(self, formatter, source_obj, dest_format):
        repos_mgr = RepositoryManager(self.env)
        try: #0.12+
            repos_name, repos,source_obj = repos_mgr.get_repository_by_path(source_obj)
        except AttributeError, e: #0.11
            repos = repos_mgr.get_repository(formatter.req.authname)
        path, rev = _split_path(source_obj)
        node = repos.get_node(path, rev)
        out = node.get_content().read()
        if dest_format is None:
            dest_format = node.content_type or get_mimetype(path, out)
        ctxt = Context.from_request(formatter.req, 'source', path)
        
        return out, ctxt, dest_format
    
def _split_path(source_obj):
    if '@' in source_obj:
        path, rev = source_obj.split('@', 1)
    else:
        path, rev = source_obj, None
    return path, rev    
    