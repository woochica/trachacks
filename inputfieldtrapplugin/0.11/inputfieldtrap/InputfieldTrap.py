"""A simple html INPUT field that acts as a trap for spambots. The general spam-bot
fills in any field there is, ignoring CSS rules and even sometimes falling in a
INPUT TYPE=hidden trap field.

This plugin was based on MathCaptcha by Rob McMullen, which in turn based
database setup code off of BSD licensed TicketModerator by John D. Siirola.

Author: (Absent. This is the first and final version for trac-0.11.x)
License: BSD, like Trac itself
"""
import re
import sys
import time
import urllib

from trac.core import *
from trac.ticket.api import ITicketManipulator
from trac.web.api import ITemplateStreamFilter
from trac.wiki.api import IWikiPageManipulator

from genshi.builder import tag
from genshi.filters.transform import Transformer

class InputfieldTrapPlugin(Component):
    implements(ITicketManipulator, ITemplateStreamFilter, IWikiPageManipulator)

    def get_content(self, req):
        """Returns the Genshi tags for the HTML INPUT trap element"""
        content = tag.div()(
            tag.input(type='hidden', name='keepempty', value='')
            )
        return content
    
    def validate_inputfieldtrap(self, req):
        """Validates that trap field is empty"""
        field = req.args.get('keepempty')
        if field:
            return [(None, "You seem to be a bot - if so, go away!")]
        return []
    
    # ITemplateStreamFilter interface

    def filter_stream(self, req, method, filename, stream, data):
        """Return a filtered Genshi event stream, or the original unfiltered
        stream if no match.

        `req` is the current request object, `method` is the Genshi render
        method (xml, xhtml or text), `filename` is the filename of the template
        to be rendered, `stream` is the event stream and `data` is the data for
        the current template.

        See the Genshi documentation for more information.
        """

        # Insert the hidden field right before the submit buttons
        stream = stream | Transformer('//div[@class="buttons"]').before(self.get_content(req))
        return stream
    
    
    # ITicketManipulator interface
    
    def validate_ticket(self, req, ticket):
        """Validate a ticket after it's been populated from user input.
        
        Must return a list of `(field, message)` tuples, one for each problem
        detected. `field` can be `None` to indicate an overall problem with the
        ticket. Therefore, a return value of `[]` means everything is OK."""
		
        return self.validate_inputfieldtrap(req)   # if req.authname == "anonymous"
    
	
    # IWikiPageManipulator interface
    
    def validate_wiki_page(self, req, page):
        """Validate a wiki page after it's been populated from user input.
        
        Must return a list of `(field, message)` tuples, one for each problem
        detected. `field` can be `None` to indicate an overall problem with the
        ticket. Therefore, a return value of `[]` means everything is OK."""
        
        return self.validate_inputfieldtrap(req) # if req.authname == "anonymous"
