"""
$Id$
$HeadURL$

Copyright (c) 2006 Peter Kropf. All rights reserved.

Module documentation goes here.
"""



__revision__  = '$LastChangedRevision$'
__id__        = '$Id$'
__headurl__   = '$HeadURL$'
__docformat__ = 'restructuredtext'
__version__   = '0.1.0'


from trac.core import *
from trac.web.chrome import INavigationContributor
from trac.web.main import IRequestHandler
from trac.util import escape, Markup


class BuildbotModule(Component):
    implements(INavigationContributor, IRequestHandler)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'buildbot'
                
    def get_navigation_items(self, req):
        yield 'mainnav', 'buildbot', Markup('<a href="%s">Buildbot</a>', self.env.href.buildbot())

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/buildbot'
    
    def process_request(self, req):
        req.send_response(200)
        req.send_header('Content-Type', 'text/plain')
        req.end_headers()
        req.write('Buildbot information to go here...')
