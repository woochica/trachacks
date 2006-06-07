from trac.core import *
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
 
    implements(INavigationContributor, ITemplateProvider)
    
    ctxtnav_adders = ExtensionPoint(ICtxtnavAdder)
    
    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return '' # This is never called
        
    def get_navigation_items(self, req):
        evil_js = self.env.href('ctxtnavadd','js','ctxtnavadd.js')
        if have_aj:
            add_javascript(req, evil_js)
        else:
            self._add_js_inc(req, self.env.href.chrome(evil_js))
        self._add_js(req,self._make_js(req))
        
        return [] # This returns no buttons
        
    # ITemplateProvider methods    
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        #return [resource_filename(__name__, 'templates')]
        return []

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
    def _add_js(self, req, data):
        """Add javascript to a page via hdf['project.footer']"""
        footer = req.hdf['project.footer']
        footer += data
        req.hdf['project.footer'] = Markup(footer)
    
    def _add_js_inc(self, req, file):
        """Add a javascript include via hdf['project.footer']"""
        self._add_js(req, inc_script%file)

    def _make_js(self, req):
        """Generate the needed Javascript."""
        adds = []
        for adder in self.ctxtnav_adders:
            if adder.match_ctxtnav_add(req):
                for add in adder.get_ctxtnav_adds(req):
                    if isinstance(add, Markup):
                        adds.append(Markup(add.replace("'","\\'")))
                    else:
                        href, text = add
                        adds.append(Markup('<a href="%s">%s</a>'%(href,Markup.escape(text,False))))
        js = ""
        for add in adds:
            js += "add_ctxtnav('%s');\n"%add
        return """<script type="text/javascript">%s</script>"""%js
    
