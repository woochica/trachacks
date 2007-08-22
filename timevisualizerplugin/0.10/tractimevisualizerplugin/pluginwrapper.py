"""This module provides component entry points for Trac. Actual implementations are in other module.
DEVELOPING flag can be used to switch between modes - if true, the implementation is reloaded on
each http request - otherwise server boot is needed to reload changes"""

from trac.core import *
from trac.web.api import IRequestHandler
from trac.core import *
from trac.wiki.macros import WikiMacroBase

class SVGRenderer(Component):
    """This component draws customizable burndown graphs from history data provided by
       TimingAndEstimationPlugin. Dynamic graphs can be easily embedded to wiki pages."""
    implements(IRequestHandler)

    def __init__(self):
        self.anonymous_request = False
        self.use_template = False

    def match_request(self, req):
        """Return whether the handler wants to process the given request."""
        return req.path_info.find('/tractimevisualizer') == 0;

    def process_request(self, req):
        req.perm.assert_permission('TICKET_VIEW')
        DEVELOPING = False

        import impl
        if DEVELOPING:
            reload(impl)

        return impl.process_request(self, req)

class BurnDownMacro(WikiMacroBase):
    """Renders iframe sets the content to be svg created by burndownimage.

Takes three options: width, height and query. Query is the the format of http query and is passed to SVGRenderer.

Example macro usage:
{{{
[[BurnDown(width=600,height=200,query=targetmilestone=milestone1&dateend=8/31/07)]]
}}}
"""
    def render_macro(self, req, name, content):
        options = {}
        if content:
            args = content.split(',')
            for arg in args:
                i = arg.index('=')
                options[arg[:i]] = arg[i+1:]
        return '<iframe frameborder="1" src="%s/tractimevisualizer?%s" width="%s" height="%s"></iframe>' \
            % (req.base_path, options.get('query', ''), options.get('width', '600'), options.get('height', '200'))
