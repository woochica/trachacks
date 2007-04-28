from trac.core import *
from trac.web.chrome import ITemplateProvider, add_script
from trac.web.api import IRequestHandler, IRequestFilter
from genshi.core import Markup
from genshi.builder import tag

from ctxtnavadd.api import ICtxtnavAdder

inc_script = """<script type="text/javascript" src="%s"></script>""" 

class ReqProxy(object):
    """A proxy to intercept req.path_info."""
    
    def __init__(self, req, path_info):
        object.__setattr__(self, '_req', req)
        object.__setattr__(self, 'path_info', path_info)
        
    def __getattr__(self, key):
        return getattr(self._req, key)
        
    def __setattr__(self, key, value):
        setattr(self._req, key, value)

class CtxtnavAddModule(Component):
    """An evil module that adds buttons to the ctxtnav bar of other plugins."""
 
    implements(ITemplateProvider, IRequestFilter, IRequestHandler)
    
    ctxtnav_adders = ExtensionPoint(ICtxtnavAdder)
    
    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return '' # This is never called
        
    def get_navigation_items(self, req):
        evil_js = '/'.join(['ctxtnavadd','js','ctxtnavadd.js'])
        #add_script(req, evil_js)
        #self._add_js(req,self._make_js(req))
        
        return [] # This returns no buttons
        
    # ITemplateProvider methods    
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('ctxtnavadd', resource_filename(__name__, 'htdocs'))]

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/ctxtnavadd')
            
    def process_request(self, req):
        data = {}        
        real_path = req.path_info[11:]
        fake_req = ReqProxy(req, real_path)
        data['adds'] = self._get_adds(fake_req)
        return 'ctxtnavadd.js', data, 'text/plain'
            
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
        
    def post_process_request(self, req, template, data, content_type):
        add_script(req, 'ctxtnavadd/js/ctxtnavadd.js')
        add_script(req, '/ctxtnavadd'+req.path_info)
        #self._add_js(req, data, self._make_js(req))
        return template, data, content_type        

    # Internal methods
    def _get_adds(self, req):
        """Find all links to add."""
        for adder in self.ctxtnav_adders:
            if adder.match_ctxtnav_add(req):
                for add in adder.get_ctxtnav_adds(req):
                    if isinstance(add, Markup):
                        yield Markup(add.replace("'","\\'"))
                    else:
                        yield tag.a(add[1], href=Markup(add[0]))

    

