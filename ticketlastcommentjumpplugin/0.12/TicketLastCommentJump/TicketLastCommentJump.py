#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

from genshi.builder import tag

from trac.core import *
from trac.web.api import ITemplateStreamFilter
from genshi.filters.transform import Transformer
from genshi.template import MarkupTemplate

from trac.util.translation import domain_functions

_, tag_, N_, add_domain = domain_functions('TicketLastCommentJump', ('_', 'tag_', 'N_', 'add_domain'))

class TicketLastCommentJump(Component):
    implements( ITemplateStreamFilter )

    def __init__(self):
        from pkg_resources import resource_filename
        locale_dir = resource_filename(__name__, 'locale')
        add_domain(self.env.path, locale_dir)

    # ITemplateStreamFilter methods
    """Filter a Genshi event stream prior to rendering."""

    def filter_stream( self, req, method, filename, stream, data ):
        if filename != 'ticket.html':
            return stream

        if data.has_key('ticket') and data.has_key('changes'):
            clist = [x for x in data['changes'] if x.has_key('cnum')]
            cnum = len(clist)
            if cnum > 0:
                link = '<div class="trac-topnav" sizcache="0" sizset="17">'\
                   + '[<a href="#comment:' + str(cnum) + '">'\
                   + _('Last Comment')\
                   + '</a>]'\
                   + '</div>\n'
                return stream | Transformer( '//div[@id="main"]/div[@class="ticket"]/div[@class="trac-topnav"]' )\
                      .before( MarkupTemplate( link ).generate() )
        return stream


