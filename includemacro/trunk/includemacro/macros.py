# TracIncludeMacro macros
import urllib2
from StringIO import StringIO

from genshi.core import escape
from genshi.filters.html import HTMLSanitizer
from genshi.input import HTMLParser, ParseError
from trac.core import *
from trac.mimeview.api import Mimeview, get_mimetype, Context
from trac.perm import IPermissionRequestor
from trac.versioncontrol.api import RepositoryManager
from trac.wiki.macros import WikiMacroBase
from trac.wiki.formatter import system_message
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
            page = WikiPage(self.env, source_obj)
            if not 'WIKI_VIEW' in formatter.perm(page.resource):
                return ''
            if not page.exists:
                return system_message('Wiki page %s does not exist' % source_obj)
            out = page.text
            ctxt = Context.from_request(formatter.req, 'wiki', source_obj)
        elif source_format == 'source':
            out, ctxt, dest_format = self._get_source(formatter, source_obj, dest_format)
        else:
            # RFE: Add ticket: and comment: sources. <NPK>
            # RFE: Add attachment: source. <NPK>
            return system_message('Unsupported include source %s'%source)
        
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
    
    def _get_source(self, formatter, source_obj, dest_format):
        if not formatter.perm.has_permission('FILE_VIEW'):
            return ''
        repos_mgr = RepositoryManager(self.env)
        try: #0.12+
            (repos_name,repos,source_obj) = repos_mgr.get_repository_by_path(source_obj)
        except AttributeError, e: #0.11
            repos = repos_mgr.get_repository(formatter.req.authname)
        node = repos.get_node(source_obj)
        out = node.get_content().read()
        if dest_format is None:
            dest_format = node.content_type or get_mimetype(source_obj, out)
        ctxt = Context.from_request(formatter.req, 'source', source_obj)
        
        return out, ctxt, source_obj
    