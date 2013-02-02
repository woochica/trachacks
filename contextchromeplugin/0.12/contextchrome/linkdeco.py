#!/usr/bin/env python
# -*- coding: utf-8 -*-

from trac.core import Component, implements
from trac.ticket.api import TicketSystem
from trac.web.api import IRequestHandler, IRequestFilter
from trac.config import ListOption, IntOption
from trac.util import Ranges
from genshi.builder import Element
from trac.wiki.api import WikiSystem
from trac.wiki.model import WikiPage
from datetime import datetime
from trac.web.chrome import ITemplateProvider, add_stylesheet
from pkg_resources import ResourceManager


class TicketLinkDecorator(Component):
    """ set css-class to ticket link as ticket field value. field name can set in [ticket]-decorate_fields in trac.ini"""
    implements(IRequestHandler)

    wrapped = None

    decorate_fields = ListOption('ticket', 'decorate_fields', default='type',
        doc=""" comma separated List of field names to add css class of ticket link.
            (Provided by !ContextChrome.!TicketLinkDecorator) """)

    def __init__(self):
        Component.__init__(self)
        if not self.wrapped:
            self.wrap()

    def wrap(self):
        ticketsystem = self.compmgr[TicketSystem]

        def _format_link(*args, **kwargs):  # hook method
            element = self.wrapped(*args, **kwargs)
            if isinstance(element, Element):
                class_ = element.attrib.get('class')
                if class_ and element.attrib.get('href'):  # existing ticket
                    deco = self.get_deco(*args, **kwargs) or []
                    element.attrib = element.attrib | [('class', ' '.join(deco + [class_]))]
            return element
        self.wrapped = ticketsystem._format_link
        ticketsystem._format_link = _format_link

    def get_deco(self, formatter, ns, target, label, fullmatch=None):
        link, params, fragment = formatter.split_link(target)  # @UnusedVariable
        r = Ranges(link)
        if len(r) == 1:
            num = r.a
            ticket = formatter.resource('ticket', num)
            from trac.ticket.model import Ticket
            if Ticket.id_is_valid(num) and \
                    'TICKET_VIEW' in formatter.perm(ticket):
                ticket = Ticket(self.env, num)
                fields = self.config.getlist('ticket', 'decorate_fields')
                return ['%s_is_%s' % (field, ticket.values[field]) for field in fields if field in ticket.values]

    # IRequestHandler Methods
    def match_request(self, req):
        return False

    def process_request(self, req):
        pass


class WikiLinkNewDecolator(Component):
    """ set \"new\" css-class to wiki link if the page is young. age can set in [wiki]-wiki_new_info_second in trac.ini"""
    implements(IRequestHandler)

    wrapped = None

    wiki_new_info_day = IntOption('wiki', 'wiki_new_info_second', '432000',
        doc=u"""age in seconds to add new icon. (Provided by !ContextChrome.!WikiLinkNewDecolator) """)

    def __init__(self):
        Component.__init__(self)
        if not self.wrapped:
            self.wrap()

    def wrap(self):
        wikisystem = self.compmgr[WikiSystem]

        def _format_link(*args, **kwargs):  # hook method
            element = self.wrapped(*args, **kwargs)
            if isinstance(element, Element):
                class_ = element.attrib.get('class')
                if class_ and element.attrib.get('href'):  # existing ticket
                    deco = self.get_deco(*args, **kwargs) or []
                    element.attrib = element.attrib | [('class', ' '.join(deco + [class_]))]
            return element
        self.wrapped = wikisystem._format_link
        wikisystem._format_link = _format_link

    def get_deco(self, formatter, ns, pagename, label, ignore_missing,
                     original_label=None):
        wikipage = WikiPage(self.env, pagename)
        if not wikipage.time:
            return
        now = datetime.now(formatter.req.tz)
        delta = now - wikipage.time
        limit = self.config.getint('wiki', 'wiki_new_info_second')
        if limit < delta.days * 86400 + delta.seconds:
            return
        return ['new']

    # IRequestHandler Methods
    def match_request(self, req):
        return False

    def process_request(self, req):
        pass


class InternalStylesheet(Component):
    """ Use internal stylesheet. Off to use your own site.css for \".new\" css-class."""
    implements(IRequestFilter, ITemplateProvider)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        add_stylesheet(req, "contextchrome/css/contextchrome.css")
        return handler

    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('contextchrome', ResourceManager().resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
