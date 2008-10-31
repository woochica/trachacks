"""
LoomingClouds:
a plugin for Trac
http://trac.edgewall.org
"""

from genshi.filters.transform import Transformer

from trac.core import *
from trac.mimeview import Context
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import add_stylesheet
from trac.wiki.formatter import Formatter
from tractags.macros import TagCloudMacro

class LoomingClouds(Component):

    implements(ITemplateStreamFilter)

    ### methods for ITemplateStreamFilter

    """Filter a Genshi event stream prior to rendering."""

    def filter_stream(self, req, method, filename, stream, data):
        """Return a filtered Genshi event stream, or the original unfiltered
        stream if no match.

        `req` is the current request object, `method` is the Genshi render
        method (xml, xhtml or text), `filename` is the filename of the template
        to be rendered, `stream` is the event stream and `data` is the data for
        the current template.

        See the Genshi documentation for more information.
        """

        if filename == 'ticket.html':

            add_stylesheet(req, 'tags/css/tractags.css')
            formatter = Formatter(self.env, Context.from_request(req))
            macro = TagCloudMacro(self.env)
            cloud = macro.expand_macro(formatter, 'TagCloud', '')

            stream |= Transformer("//input[@id='field-keywords']").after(cloud)

        return stream
