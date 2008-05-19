# -*- coding: utf-8 -*-

"""
0.11dev rewrite of original ShowPath functionality.  Replaces 
the global "Start Page" link with a path of links for 
hierarchical pages.
e.g., http://mytrac.com/wiki/ParentPage/ChildPage/GrandchildPage
..would create a ShowPath of 
Start Page / ParentPage / ChildPage / GrandchildPage
..where all are links except for the current, GrandchildPage.

 - http://trac.edgewall.org/wiki/MacroBazaar#ShowPath
 - http://trac-hacks.org/wiki/TracShowPathPatch

Just drop in your trac/<projectname>/plugins dir.

Supports one optional trac.ini setting, sep_character, which
specifies the character to use in the path display:
    [showpath]
    sep_character = »
The default is a forward slash (/); note that no matter what character
is specified, it will always be rendered with a single space on
either side.  If you specify a string of more than one character,
only the first non-whitespace character will be used.

2007 Morris - gt4329b@pobox.com
rfmorris on irc://freenode/trac

"""

from pprint import pprint, pformat

from trac.core import *
#from trac.ticket.query import TicketQueryMacro
#from trac.wiki.macros import WikiMacroBase
from trac.wiki.api import parse_args
from trac.web import IRequestHandler, IRequestFilter, ITemplateStreamFilter

## genshi imports (genshi.filters.Transformer requires Genshi 0.5+)
##  http://genshi.edgewall.org/
from genshi.builder import tag
from genshi.filters import Transformer
from genshi.core import TEXT
from genshi.input import HTML

_DEFAULT_SEP = '/'

class ShowPath(Component):
    implements(ITemplateStreamFilter)

    def __init__(self, *args, **kwargs):
        Component.__init__(self, *args, **kwargs)
        self.sep_character = self.config.get(
            'showpath', 'sep_character', _DEFAULT_SEP).strip()
        # QA our possibly-user-supplied separator char
        if self.sep_character == '':
            self.sep_character = _DEFAULT_SEP
        self.sep_character = self.sep_character[0]
            

    # ITemplateStreamFilter methods
    
    def filter_stream(self, req, method, filename, stream, data):
        page_path = req.args.get('page',None)
        if not page_path or page_path == 'WikiStart':
            return stream

        page_paths = page_path.split('/')
        # reverse it so we can .pop() in the necessary order
        page_paths.reverse()

        _links = []
        _base = "/wiki"
        _prev_path = ""        
        while page_paths:
            page_path = page_paths.pop()
            _prev_path += "/" + page_path
            _link = None
            if page_paths:
                _link = _base + _prev_path
            t = (page_path, _link)
            _links.append(t)
        # always prepend the default start page link
        _links = [('Start Page','/wiki/WikiStart')] + _links
        
        r = []
        for link in _links:
            text, _href = link
            if _href:
                r += tag(tag.a(text, href=_href), 
                            ' %s ' % self.sep_character)
            else:
                # last entry in list
                #  ..so _href is None 
                #  ..so no sep char appended
                r += tag(text)
                
        # http://genshi.edgewall.org/wiki/GenshiRecipes/HtmlTransform
        # http://genshi.edgewall.org/browser/trunk/genshi/filters/transform.py
        t1 = Transformer(
            "//div[@id='ctxtnav']//a[@href='/wiki/WikiStart']") \
                .replace(r)
        stream |= t1
        return stream
