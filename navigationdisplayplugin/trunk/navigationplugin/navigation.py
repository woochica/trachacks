# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Franz Mayer <franz.mayer@gefasoft.de>
#
# "THE BEER-WARE LICENSE" (Revision 42):
# <franz.mayer@gefasoft.de> wrote this file.  As long as you retain this 
# notice you can do whatever you want with this stuff. If we meet some day, 
# and you think this stuff is worth it, you can buy me a beer in return. 
# Franz Mayer
#
# Author: Franz Mayer <franz.mayer@gefasoft.de>

from trac.core import Component, implements
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.util.translation import domain_functions
from trac.web.chrome import ITemplateProvider, add_stylesheet, Chrome,\
    add_warning
from trac.config import ChoiceOption, Option
from genshi.filters import Transformer
from genshi import HTML
from pkg_resources import resource_filename #@UnresolvedImport
from genshi.builder import tag
from trac.wiki.api import WikiSystem
from genshi.core import Markup
from trac.util import as_int

_, tag_, N_, add_domain = \
    domain_functions('navigationplugin', '_', 'tag_', 'N_', 'add_domain')

SESSION_KEYS = {'nav': 'display_nav', 
                'wiki': 'wiki.href', 
                'tickets': 'tickets.href'}

DISPLAY_CHOICES = ['normal', 'buttom_ctx_menu', 'fixed_menu']
CHOICES_DOC = {'normal': 
               _("Trac default"), 
               'buttom_ctx_menu': 
               _("Display another context menu at the buttom of page"),
               'fixed_menu': 
               _("Display banner and menu fixed on top of page "
                 "(under development)")}

class Navigation(Component):
    """This plugin enables user to choose, if she uses a different (means more
elegant way) display of naviagtion bar.

Type of displaying menu. Possible types are:
`normal` (default): No integration - ''leaves menu as in Trac standard'' 
`fixed_menu`: fixes menu incl. context navigation on top 
of browser window (under DEVELOPMENT!!),
`buttom_ctx_menu`: adds context menu at buttom of page, if available
"""
    implements(IRequestFilter, ITemplateProvider, ITemplateStreamFilter)

    display_navigation = ChoiceOption('trac', SESSION_KEYS['nav'],
        choices=DISPLAY_CHOICES,
        doc="""Type of displaying menu. Possible types are:
`normal` (default): No integration - ''leaves menu as in Trac standard'' 
`fixed_menu`: fixes menu incl. context navigation on top 
of browser window (under DEVELOPMENT!!),
`buttom_ctx_menu`: adds context menu at buttom of page, if available""")
    wiki_link = Option('mainnav', SESSION_KEYS['wiki'], default=None, doc='',
                 doc_domain='tracini')
    ticket_link = Option('mainnav', SESSION_KEYS['tickets'], default=None, doc='',
                 doc_domain='tracini')
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        display = self.get_display(req)
        
        if not display == 'normal':
            # only do something if specified
            if 'fixed_menu' == display:
                add_stylesheet(req, 'navpl/fixed_menu.css')
            
        return (template, data, content_type)
        
    # ITemplateProvider methods
    def get_templates_dirs(self):
        return
    
    def get_htdocs_dirs(self):
        return [('navpl', resource_filename(__name__, 'htdocs'))]  
    
    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        display = self.get_display(req)
        self.__inject_links(req, data['chrome'])
 
        if not display == 'normal':
            # non-standard"
            if 'fixed_menu' == display:
                return self._add_style_attributes(req, stream)
            elif 'buttom_ctx_menu' == display:
                return self._add_buttom_ctx_menu(req, stream)
        
        return stream

    def __inject_links(self, req, chrome_data):
        if chrome_data and chrome_data.has_key('nav'):
            nav = chrome_data['nav']
            if nav and nav.has_key('mainnav'):
                repl_links = self.get_repl_links(req)
                if len(repl_links) > 0: 
                    mainnav = nav['mainnav']
                    for nav in mainnav:
#                        self.log.info('nav: %s' % nav)
                        if nav.has_key('name') \
                        and nav['name'] in repl_links.keys():
                            self.replace_links(req, nav, 
                                               repl_links[nav['name']])
                            
    def replace_links(self, req, nav, new_link):
        wiki_label = nav['label']
        name = '---'
        try:
            name = wiki_label.children
            if nav['name'] == 'wiki':
                nav['label'] = tag.a(name,
                                     href=req.href.wiki(new_link))
            elif nav['name'] == 'tickets':
                if new_link == 'report':
                    nav['label'] = tag.a(name, href=req.href.report())
                elif new_link == 'query':
                    nav['label'] = tag.a(name, href=req.href.query())
                else:
                    nav['label'] = tag.a(name, href=req.href.report(new_link))
        except Exception, e:
            self.log.error(e)
    
    def get_repl_links(self, req):
        repl_links = {}
        wiki_href = self.get_wiki_href(req)
        if wiki_href != '':
            repl_links['wiki'] = wiki_href
        ticket_href = self.get_ticket_href(req)
        if ticket_href != '':
            repl_links['tickets'] = ticket_href
        return repl_links
    
    def get_display(self, req):
        return self.__get_pref_value(req, 'nav') or self.display_navigation
    
    def get_wiki_href(self, req):
        return self.__get_pref_value(req, 'wiki') or self.wiki_link
    
    def get_ticket_href(self, req):
        ticket_href = self.__get_pref_value(req, 'tickets') or self.ticket_link
        return self.__get_report_id(ticket_href)
        
    def __get_report_id(self, ticket_href):
        if ticket_href:
            idx = ticket_href.find('/report/')
            if idx > -1:
                ticket_href = ticket_href[idx+8:]
        return ticket_href
    
    def __get_pref_value(self, req, session_key):
#        self.save(req)
        if req.session.has_key(SESSION_KEYS[session_key]):
            return req.session[SESSION_KEYS[session_key]]
        return None
    
    def save(self, req):
        if req.args and req.args.has_key('action') \
        and req.args['action'] == 'save':
            for key in SESSION_KEYS.values():
                if req.args.has_key(key):
                    if key == 'wiki.href':
                        wiki_href = req.args[key]
                        if wiki_href == '':
                            req.session[key] = ''
                            continue
                        validated = WikiSystem(self.env).has_page(wiki_href)
                        if validated:
                            req.session[key] = req.args[key]
                        else:
                            add_warning(req, Markup(tag.span(Markup(_(
                                "%(page)s is not a valid Wiki page",
                                page=tag.b(wiki_href)
                                )))))
                    elif key == 'tickets.href':
                        ticket_href = req.args[key]
                        if ticket_href == '':
                            req.session[key] = ''
                            continue
                        reports = self.get_report_list()
                        self.log.info('reports: %s' % reports)
                        if ticket_href in ('report', 'query') \
                        or as_int(ticket_href, 0) in reports:
                            req.session[key] = req.args[key]
                        else:
                            add_warning(req, Markup(tag.span(Markup(_(
                                "%(report)s is not a valid report",
                                report=tag.b(ticket_href)
                                )))))
                    else:
                        req.session[key] = req.args[key]
    
    def get_report_list(self):
        # copied from report.py, _render_list
        rows = self.env.db_query("""
                SELECT id FROM report ORDER BY %s %s
                """ % ('id', 'DESC'))
        reports = [rid[0] for rid in rows]
        return reports
    
    def get_session_keys(self):
        return SESSION_KEYS.values()
                    
    def get_system_default_tickets_href(self):
        return self.__get_report_id(self.ticket_link) \
            or self.env.abs_href.report()
                    
    def get_system_default_wiki_href(self):
        return self.wiki_link or self.env.abs_href.wiki()
                    
    def get_system_default_display(self):
        return self.display_navigation
    
    def get_display_choices(self):
        return DISPLAY_CHOICES
        
    def _add_style_attributes(self, req, stream):
        logo = Chrome(self.env).get_logo_data(self.env.abs_href)
        
        if logo:
            height = logo['height']
#            self.log.debug("Logo height: %s" % height)
            if height:
                style_css = '';
                height += 25
                style_css += '#mainnav, #ctxtnav, #pagepath {top: %ipx;}' % height
                height += 50
                style_css += '#content, #notice, #warning, #altlinks, #altlinks, #footer {top: %ipx;}' % height
                style_css = '@media screen { %s }' % style_css
                style_tag = tag.style(style_css, type="text/css")
                stream |= Transformer('.//head').append(style_tag)
            
            # TODO: get logo-src and finding how big it is

            return stream
        # TODO: what if there has not been any image specified?
    
    def _add_buttom_ctx_menu(self, req, stream):
        if req.chrome.has_key('ctxtnav'):
            ctxtnav = req.chrome['ctxtnav']
            ctx_str = ""
            for i, entry in enumerate(ctxtnav):
                if i == 0:
                    ctx_str += "<li class='first'>"
                elif i == len(ctxtnav) -1:
                    ctx_str += "<li class='last'>"
                else:
                    ctx_str += "<li>"
                
                ctx_str = "%s%s</li>" % (ctx_str, entry)
                
#            self.log.info("ctx_str %s" % ctx_str)
            html = HTML( "<div id='ctxtnavbottom' class='nav'><ul>%s"
                         "</ul></div>" % ctx_str )
            stream |= Transformer('.//div[@id="help"]').before( html )
            return stream
        return stream
