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


_, tag_, N_, add_domain = \
    domain_functions('navigationplugin', '_', 'tag_', 'N_', 'add_domain')

SESSION_KEYS = {'nav': 'display_nav', 'wiki': 'wiki.href'}
DISPLAY_CHOICES = ['normal', 'buttom_ctx_menu', 'fixed_main_ctx_menu_DEV']

class Navigation(Component):
    """This plugin enables user to choose, if she uses a different (means more
elegant way) display of naviagtion bar.

Type of displaying menu. Possible types are:
`normal` (default): No integration - ''leaves menu as in Trac standard'' 
`fixed_main_ctx_menu_DEV`: fixes menu incl. context navigation on top 
of browser window (under DEVELOPMENT!!),
`buttom_ctx_menu`: adds context menu at buttom of page, if available
"""
    implements(IRequestFilter, ITemplateProvider, ITemplateStreamFilter)

    display_navigation = ChoiceOption('trac', SESSION_KEYS['nav'],
        choices=DISPLAY_CHOICES,
        doc="""Type of displaying menu. Possible types are:
`normal` (default): No integration - ''leaves menu as in Trac standard'' 
`fixed_main_ctx_menu_DEV`: fixes menu incl. context navigation on top 
of browser window (under DEVELOPMENT!!),
`buttom_ctx_menu`: adds context menu at buttom of page, if available""")
    wiki_link = Option('mainnav', SESSION_KEYS['wiki'], default=None, doc='',
                 doc_domain='tracini')
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        display = self.get_display(req)
        
        if not display == 'normal':
            # only do something if specified
            if 'fixed_main_ctx_menu_DEV' == display:
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
            if 'fixed_main_ctx_menu_DEV' == display:
                return self._add_style_attributes(req, stream)
            elif 'buttom_ctx_menu' == display:
                return self._add_buttom_ctx_menu(req, stream)
        
        return stream

    def __inject_links(self, req, chrome_data):
        wiki_href = self.get_wiki_href(req)
        
        if not wiki_href == '' and chrome_data and chrome_data.has_key('nav'):
            nav = chrome_data['nav']
#            links = chrome_data['links'] # did not work
            
            if nav and nav.has_key('mainnav'):
                mainnav = nav['mainnav']
                for nav in mainnav:
                    if nav.has_key('name') and nav['name'] == 'wiki':
                        wiki_label = nav['label']
                        name = '---'
                        try:
                            name = wiki_label.children
                        except Exception, e:
                            self.log.error(e)
                        nav['label'] = tag.a(name,href=req.href.wiki(wiki_href))
    
    def get_display(self, req):
        return self.__get_pref_value(req, 'nav') or self.display_navigation
    
    def get_wiki_href(self, req):
        return self.__get_pref_value(req, 'wiki') or self.wiki_link
    
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
                    if key in ('wiki.href'):
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
                    else:
                        req.session[key] = req.args[key]
    
    def get_session_keys(self):
        return SESSION_KEYS.values()
                    
    def get_system_default_wiki_href(self):
        return self.wiki_link
                    
    def get_system_default_display(self):
        return self.display_navigation
    
    def get_display_choices(self):
        return DISPLAY_CHOICES
        
    def _add_style_attributes(self, req, stream):
        logo = Chrome(self.env).get_logo_data(self.env.abs_href)
        
        if logo:
            height = logo['height']
#            self.log.debug("Logo height: %s" % height)
            if not height:
                # TODO: get logo-src and finding how big it is 
                return stream
            height += 8
            stream |= Transformer('.//div[@id="mainnav"]') \
                .attr('style', 'top: %ipx' % height)
            height += 25
            stream |= Transformer('.//div[@id="ctxtnav"]') \
                .attr('style', 'top: %ipx' % height)
            height += 10
            #===================================================================
            # stream |= Transformer('.//div[@id="pagepath"]') \
            #    .attr('style', 'top: %ipx' % height)
            #===================================================================
            stream |= Transformer('.//div[@id="warning"]') \
                .attr('style', 'top: %ipx' % height)
            stream |= Transformer('.//div[@id="content"]') \
                .attr('style', 'top: %ipx' % height)
            stream |= Transformer('.//div[@id="altlinks"]') \
                .attr('style', 'top: %ipx' % height)
            stream |= Transformer('.//div[@id="footer"]') \
                .attr('style', 'top: %ipx' % height)
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
