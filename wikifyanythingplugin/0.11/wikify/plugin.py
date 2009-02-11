from trac.core import *
from trac.mimeview import *
from trac.web.api import ITemplateStreamFilter
from trac.wiki.formatter import *
from trac.config import Option, IntOption, ListOption, BoolOption
from genshi.builder import tag
from genshi.core import Markup
from genshi.filters.transform import Transformer, TEXT

class WikifyAnythingPlugin(Component):
    """
        This plugin allows you to create custom ticket fields that
        include wiki formatting. The field type should remain as "text".
        Just add a new option called "wikiformat" and set its value
        to "true".
        
        Here's an example for a field that would link to the business
        requirements document:
        
        [ticket-custom]
        busreq_link = text
        busreq_link.label = Business Requirements
        busreq_link.wikiformat = true

        You can then create a new ticket and set the custom field
        to some wiki-formatted text, like this:
        
            [wiki:MyProjectRequirements] '''(incomplete)'''

        In the ticket summary, the text will include the link to the
        MyProjectRequirements wiki page, followed by the word "(incomplete)"
        in bold.
    """

    implements(ITemplateStreamFilter)

    def __init__(self):
        config = self.config['wikify']
        pages = {}
        for option, value in config.options():
            if '.' not in option:
                continue
            patterns = value.split(',')
            pages[option] = patterns
        self.pages = pages

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        def _map_wikify(item):
            return wiki_to_oneliner(item, self.env, req=req)
        if filename in self.pages.keys():
            for pattern in self.pages[filename]:
                stream = stream | Transformer(pattern).map(_map_wikify, TEXT) 
        return stream
