# FlashView plugin

from StringIO import StringIO
from cgi import escape as escapeHTML

import re
import os
from trac.core import *
from trac.wiki.api import IWikiMacroProvider

class FlashViewMacro(Component):
    """ FlashView Macro """
    
    implements(IWikiMacroProvider)
    
    def get_macros(self):
        yield "FlashView"

    def get_macro_description(self, name):
        """Return the subclass's docstring."""
        return inspect.getdoc(self.__class__)

    def render_macro(self, req, name, content):
        # args will be null if the macro is called without parenthesis.
        if not content:
            return ''
        args = content.split(',')
        filespec = args[0]
        
        # parse filespec argument to get module and id if contained.
        parts = filespec.split(':')
        url = None
        if len(parts) == 3:                 # module:id:attachment
            if parts[0] in ['wiki', 'ticket']:
                module, id, file = parts
            else:
                raise Exception("%s module can't have attachments" % parts[0])
        elif len(parts) == 2:
            from trac.versioncontrol.web_ui import BrowserModule
            try:
                browser_links = [link for link,_ in 
                                 BrowserModule(self.env).get_link_resolvers()]
            except Exception:
                browser_links = []
            if parts[0] in browser_links:   # source:path
                module, file = parts
                rev = None
                if '@' in file:
                    file, rev = file.split('@')
                url = req.href.browser(file, rev=rev)
                raw_url = req.href.browser(file, rev=rev, format='raw')
                desc = filespec
            else: # #ticket:attachment or WikiPage:attachment
                # FIXME: do something generic about shorthand forms...
                id, file = parts
                if id and id[0] == '#':
                    module = 'ticket'
                    id = id[1:]
                elif id == 'htdocs':
                    raw_url = url = req.href.chrome('site', file)
                    desc = os.path.basename(file)
                elif id in ('http', 'https', 'ftp'): # external URLs
                    raw_url = url = desc = id+':'+file
                else:
                    module = 'wiki'
        elif len(parts) == 1:               # attachment
            # determine current object
            # FIXME: should be retrieved from the formatter...
            # ...and the formatter should be provided to the macro
            file = filespec
            module, id = 'wiki', 'WikiStart'
            path_info = req.path_info.split('/',2)
            if len(path_info) > 1:
                module = path_info[1]
            if len(path_info) > 2:
                id = path_info[2]
            if module not in ['wiki', 'ticket']:
                raise Exception('Cannot reference local attachment from here')
        else:
            raise Exception('No filespec given')
        if not url: # this is an attachment
            from trac.attachment import Attachment
            attachment = Attachment(self.env, module, id, file)
            url = attachment.href(req)
            raw_url = attachment.href(req, format='raw')
            desc = attachment.description
        
        width = int(args[1])
        height = int(args[2])
        
        buf = StringIO()
        buf.write("<object classid='clsid:D27CDB6E-AE6D-11cf-96B8-444553540000'")
        buf.write(" codebase='http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=6,0,0,0'")
        buf.write(" width='%s'" % width)
        buf.write(" height='%s'>" % height)
        buf.write("<param name='movie' value='%s'>" % raw_url)
        buf.write("<param name='quality' value='low'>")
        buf.write("<param name='play' value='true'>")
        buf.write("<embed src='%s'" % raw_url)
        buf.write(" quality='low'")
        buf.write(" width='%s'" % width)
        buf.write(" height='%s'" % height)
        buf.write(" type='application/x-shockwave-flash'")
        buf.write(" pluginspage='http://www.macromedia.com/go/getflashplayer'></embed>")
        buf.write("</object>")

        return buf.getvalue()