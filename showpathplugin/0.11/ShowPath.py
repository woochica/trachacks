from trac.web.api import IRequestFilter
from trac.web.chrome import *
from trac.core import *

from genshi.builder import tag

"""
0.11dev rewrite of original ShowPath functionality.  Replaces 
the global "Start Page" link with a path of links for 
hierarchical pages.
e.g., http://mytrac.com/wiki/ParentPage/ChildPage/GrandchildPage
..would create a ShowPath of 
Start Page / ParentPage / ChildPage / GrandchildPage
..where all are links except for the current, GrandchildPage.

 * http://trac-hacks.org/wiki/ShowPathPlugin

Just drop in your trac/<projectname>/plugins dir. If you are using
an inherited plugins_dir in Trac, that will also work to place this
file there.

Supports one optional trac.ini setting, sep_character, which
specifies the character to use in the path display:
    [showpath]
    sep_character = .
The default is a forward slash (/); note that no matter what character
is specified, it will always be rendered with a single space on
either side.  If you specify a string of more than one character,
only the first non-whitespace character will be used.

2007 Morris - gt4329b@pobox.com
rfmorris on irc://freenode/trac

2008 Modification by Jason Winnebeck
"""

_DEFAULT_SEP = '/'

class ShowPath(Component):
    implements(IRequestFilter)

    def __init__(self, *args, **kwargs):
        Component.__init__(self, *args, **kwargs)
        self.sep_character = self.config.get(
            'showpath', 'sep_character', _DEFAULT_SEP).strip()
        # QA our possibly-user-supplied separator char
        if self.sep_character == '':
            self.sep_character = _DEFAULT_SEP
        self.sep_character = self.sep_character[0]

    # IRequestFilter methods

    def post_process_request(self, req, template, data, content_type):
        page_path = req.args.get('page',None)
        if not page_path or page_path == 'WikiStart':
            return template, data, content_type

        href = req.href
        nav = req.chrome['ctxtnav']
        wikiStartIndex = None
        for i, elm in enumerate( nav ):
            if type(elm) == Element and elm.tag == 'a' and elm.attrib.get('href') == href.wiki('WikiStart'):
                wikiStartIndex = i
                break

        if wikiStartIndex is None:
            return template, data, content_type

        page_paths = page_path.split('/')
        # reverse it so we can .pop() in the necessary order
        page_paths.reverse()

        _links = []
        _prev_path = "" 
        while page_paths:
            page_path = page_paths.pop()
            _prev_path += "/" + page_path
            _link = None
            if page_paths:
                _link = href.wiki( _prev_path )
            t = (page_path, _link)
            _links.append(t)
        # always prepend the default start page link
        _links = [('Start Page',href.wiki('WikiStart'))] + _links
        
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

        nav[i] = r

        return template, data, content_type

    def pre_process_request(self, req, handler):
        return handler
