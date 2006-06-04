from trac.core import *
from trac.web.main import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.util import Markup

try:
    from trac.web.chrome import add_javascript
    have_aj = True
except ImportError:
    have_aj = False

from ctxtnavadd.api import ICtxtnavAdder

inc_script = """<script type="text/javascript" src="%s"></script>""" 

class CtxtnavAddModule(Component):
    """An evil module that adds buttons to the ctxtnav bar of other plugins."""
 
    implements(INavigationContributor, ITemplateProvider, IRequestHandler)
    
    ctxtnav_adders = ExtensionPoint(ICtxtnavAdder)
    
    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return '' # This is never called
        
    def get_navigation_items(self, req):
        evil_js = req.href('ctxtnavadd','js','ctxtnavadd.js')
        if have_aj:
            add_javascript(req, evil_js)
        else:
            self._add_javascript_footer(req, req.href.chrome(evil_js))
        self._add_javascript_footer(req,req.href.ctxtnavadd(req.path_info))
        return []
        
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/ctxtnavadd')
        
    def process_request(self, req):
        adds = []
        path_info = req.path_info[11:]
        for adder in self.ctxtnav_adders:
            if adder.match_ctxtnav_add(req, path_info):
                for add in adder.get_ctxtnav_adds(req):
                    if isinstance(add, Markup):
                        adds.append(Markup(add.replace("'","\\'")))
                    else:
                        href, text = add
                        adds.append(Markup('<a href="%s">%s</a>'%(href,Markup.escape(text,False))))
        req.hdf['ctxtnavadd.adds'] = adds
        return 'ctxtnavadd.cs', 'text/javascript'
    
    # ITemplateProvider methods    
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """
        Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        from pkg_resources import resource_filename
        return [('ctxtnavadd', resource_filename(__name__, 'htdocs'))]

    # Internal methods
    def _add_javascript_footer(self, req, file):
        """Add a javascript include via hdf['project.footer']"""
        footer = req.hdf['project.footer']
        footer += inc_script % file
        req.hdf['project.footer'] = Markup(footer)
