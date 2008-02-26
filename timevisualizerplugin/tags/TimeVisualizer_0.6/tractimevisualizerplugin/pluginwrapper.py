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

        import impl
        import tractimevisualizerplugin
        if tractimevisualizerplugin.DEVELOPER_MODE:
            reload(impl)

        return impl.process_request(self, req)

class BurnDownMacro(WikiMacroBase):
    """This macro renders iframe and sets to be svg image to be created on the fly based on given filters.

Macro takes three options: width, height and query.

Query is the the format of http query and is passed to SVGRenderer as is. Query parameters are used as follows:

To include ticket history from certain milestone/component/or certain ticket, use filters:

 * targetmilestone - only tickets data bound to given milestone name are included
 * targetcomponent - only ticket data bound to given component name are included
 * targetticket - only data in given ticket # is included

To limit burndown to certain time period, use following filters:

 * timestart - filters out ticket data before this timestamp
 * timeend - filters out ticket data after this timestamp
 * datestart - overrides timestart if passed, e.g. '8/14/07'
 * dateend - overrides timeend when passed - e.g. '8/20/07'

To override L&F of the generated svg:

 * timeinterval - time interval lines (horisontal) as seconds in graph, 3600 = 1h, 86400 = 1 day
 * hidedates - any non empty string causes start and end times not to be rendered to the graph (X-axis)
 * hidehours - any non empty string causes hours not to be rendered to the graph (Y-axis)

To use ISO8601 time in date & time parameters, override with `time_format=iso8601`

To override which fields is used to calucalte Y-value at certain change, define `calc_fields`, e.g.
`calc_fields=workleft` or `calc_fields=estimatedhours-totalhours`

Few use examples:
 1. Simplest ever case: all tickets from the whole project history
{{{
[[BurnDown]]
}}}

 1. Example macro usage using old pre 0.6 time format:
{{{
[[BurnDown(width=600,height=200,query=targetmilestone=mymilestone&dateend=8/31/07)]]
}}}

 2. Example macro usage using ISO 8601 format:
{{{
[[BurnDown(width=600,height=200,query=targetmilestone=2007-12&time_format=iso8601&datestart=2007-12&dateend=2008-01&timeinterval=1D)]]
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
