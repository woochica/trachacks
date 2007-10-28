# Created by Noah Kantrowitz on 2007-06-05.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.

import os.path
import re
import urllib
import urllib2

from trac.core import *
from trac.web.api import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
from trac.perm import IPermissionRequestor
from trac.mimeview.api import MIME_MAP as BASE_MIME_MAP
from trac.config import Option, BoolOption
from trac.util.text import to_unicode

from genshi.builder import tag
from genshi.core import Markup

# Make a copy to start us off
MIME_MAP = dict(BASE_MIME_MAP.iteritems())
MIME_MAP.update({
    'png': 'image/png',
})

class GitwebModule(Component):
    """A plugin to embed gitweb into Trac."""
    
    implements(IRequestHandler, INavigationContributor, IPermissionRequestor, ITemplateProvider)
    
    gitweb_url = Option('gitweb', 'url', doc='URL to gitweb')
    send_mime = BoolOption('gitweb', 'send_mime', default=False,
                           doc='Try to send back the correct MIME type for blob_plain pages.')
    
    patterns = [
        # (regex, replacement) 
        (r'^.*?<div class', '<div class'),
        (r'<\/body.*', ''),
        (r'git\?{1,}a=git-logo.png', 'www/images/git.png'),
        (r'[\'\"]\/git\?{0,}([^\'\"]*)', '"?\\1'),
        (r'git\.do\?(\S+)?\;a\=rss', 'git?\\1;a=rss'),
    ]
    patterns = [(re.compile(pat, re.S|re.I|re.U), rep) for pat, rep in patterns]
    
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/browser')
        
    def process_request(self, req):
        req.perm.assert_permission('BROWSER_VIEW')
        
        # Check for no URL being configured
        if not self.gitweb_url:
            raise TracError('You must configure a URL in trac.ini')
        
        # Grab the page
        urlf = urllib2.urlopen(self.gitweb_url+'?'+req.environ['QUERY_STRING'])
        page = urlf.read()
        
        # Check if this is a raw format send
        args = dict([(args or '=').split('=',1) for args in req.environ['QUERY_STRING'].split(';')])
        if args.get('a') == 'blob_plain':
            if self.send_mime:
                _, ext = os.path.splitext(args.get('f', ''))
                mime_type = MIME_MAP.get(ext[1:], 'text/plain')
            else:
                mime_type = 'text/plain'
            req.send(page, mime_type)
            
        # Check for RSS
        if args.get('a') == 'rss':
            req.send(page, urlf.info().type)
        
        # Proceed with normal page serving
        page = to_unicode(page)
        for pat, rep in self.patterns:
            page = pat.sub(rep, page)
            
        data = {
            'gitweb_page': Markup(page),
        }
        #add_link(req, 'stylesheet', 'http://dev.laptop.org/www/styles/gitbrowse.css', 'text/css')
        add_stylesheet(req, 'gitweb/gitweb.css')
        return 'gitweb.html', data, urlf.info().type

    # INavigationContributor methods
    def get_navigation_items(self, req):
        if 'BROWSER_VIEW' in req.perm:
            yield 'mainnav', 'gitweb', tag.a('Browse Source', 
                                             href=req.href.browser())
                                             
    def get_active_navigation_item(self, req):
        return 'gitweb'
        
    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'BROWSER_VIEW'
        
    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('gitweb', resource_filename(__name__, 'htdocs'))]
            
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]


