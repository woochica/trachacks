"""
LoomingClouds:
a plugin for Trac
http://trac.edgewall.org
"""

from genshi.filters.transform import Transformer

from pkg_resources import resource_filename

from trac.core import *
from trac.mimeview import Context
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import add_script
from trac.web.chrome import add_stylesheet
from trac.web.chrome import ITemplateProvider
from trac.wiki.formatter import Formatter
from tractags.macros import TagCloudMacro
from genshi.builder import tag

class LoomingClouds(Component):

    implements(ITemplateStreamFilter, ITemplateProvider)

    ### method for ITemplateStreamFilter

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

        if filename in ('ticket.html', 'agilo_ticket_new.html',):

            add_stylesheet(req, 'tags/css/tractags.css')
            add_stylesheet(req, 'loomingclouds/css/tagcloud.css')
            add_script(req, 'loomingclouds/js/tag_filler.js')
            formatter = Formatter(self.env, Context.from_request(req))
            macro = TagCloudMacro(self.env)
            cloud = macro.expand_macro(formatter, 'TagCloud', '')

            stream |= Transformer("//input[@id='field-keywords']").after(cloud).after(tag.a('More...',href='#',class_='tag-cloud-filler'))

        return stream

    ### methods for ITemplateProvider
    
    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        
        """
        return [('loomingclouds', resource_filename(__name__, 'htdocs'))]
        

    def get_templates_dirs(self):
        """Return a list of directories containing the provided template
        files.
        """
        return []

