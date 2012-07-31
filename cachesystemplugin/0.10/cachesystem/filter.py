from trac.core import *
from trac.web.api import IRequestFilter
from trac.config import Option, IntOption
from trac.wiki.web_ui import WikiModule
from trac.web.chrome import add_link, add_stylesheet
from trac.web.clearsilver import HDFWrapper

try:
    import cmemcache 
    have_cmemcache = True
except ImportError:
    import memcache
    have_cmemcache = False

class CacheFilter(Component):
    
    implements(IRequestFilter)
    
    memcached_server = Option('cache', 'memcached_server', default='localhost:11211', doc='The hostname and port for the memcached server.')
    timeout = IntOption('cache', 'timeout', default=600, doc='The time in seconds for something to age out of the cache.')
    
    def __init__(self):
        # NOTE: As speed is the idea here, the client will only be made once. This means a punt is needed to change client options. <NPK>
        server = self.memcached_server.encode('ascii')
        if ':' not in server:
            server = '%s:11211'%server
        
        if have_cmemcache:
            self.client = cmemcache.StringClient([server])
        else:
            self.client = memcache.Client([server])
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        if isinstance(handler, WikiModule):
            if req.method == 'GET' and \
               req.args.get('action', 'view') == 'view' and \
               req.args.get('format') is None and \
               req.args.get('version') is None:
                page = self.client.get(req.path_info)
                if page is not None:
                    self.log.debug('CacheFilter: Cache hit on %s', req.path_info)
                    req.__CACHED_PAGE = page
                    return self
                else:
                    req.__PLEASE_CACHE = True
            elif req.method == 'POST':
                self.client.delete(req.path_info)
        
        return handler
        
    def post_process_request(self, req, template, content_type):
        try:
            if req.__PLEASE_CACHE:
                self.client.set(req.path_info, req.hdf.getObj('wiki').writeString(), self.timeout)
        except AttributeError:
            pass
        return template, content_type
        
    # IRequestHandler methods
    def match_request(self, req):
        return False
        
    def process_request(self, req):
        # !!!: Wow, this is hackish. <NPK>
        add_stylesheet(req, 'common/css/wiki.css')
        wiki_hdf = HDFWrapper()
        wiki_hdf.readString(req.__CACHED_PAGE)
        req.hdf.copy('wiki', wiki_hdf.hdf)
        return 'wiki.cs', None
        
    