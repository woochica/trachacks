from trac.core import *
from trac.web.chrome import add_stylesheet
from trac.wiki.api import IWikiMacroProvider

from estimatorplugin.estimator import *


class EstimatorMacroProvider(Component):
    implements(IWikiMacroProvider)
    """Extension point interface for components that provide Wiki macros."""
    
    def get_macros(self):
        """Return an iterable that provides the names of the provided macros."""
        return ['Estimate']
        
    def get_macro_description(self, name):
        """Return a plain text description of the macro with the specified name.
        """
        return """ The estimate macro displays a macro and the link to change it
        """

    def estimate_macro(self,  id, req ):
        html = getHtmlEstimate(self.env, id)
        if html:
            add_stylesheet(req, "Estimate/estimate.css")
            add_stylesheet(req, "common/css/diff.css")
            html+= '<br /><a href="%s?id=%s">edit this estimate</a>' % (req.href.Estimate(), id)
        else:
            html = "Estimate Does Not Exist: %s" % (id,)
        return html
    
    def render_macro(self, req, name, content):
        """Return the HTML output of the macro (deprecated)"""
        #try:
        return self.estimate_macro(int(content), req)
        #except:
        #    return "Estimate Does Not Exist"
                                     

    def expand_macro(self, formatter, name, content):
        """Called by the formatter when rendering the parsed wiki text.
        
        (since 0.11)
        """
        #try:
        return self.estimate_macro(int(content), formatter.req)
        #except:
        #    return "Estimate Does Not Exist"
