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

from trac.core import *
from genshi.filters import Transformer
from genshi.builder import tag
from genshi import HTML
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from operator import attrgetter
from trac.util.translation import domain_functions
import re
from trac.web.chrome import ITemplateProvider, add_stylesheet, Chrome
from trac.config import ChoiceOption
from pkg_resources import resource_filename
from trac.wiki.formatter import _markup_to_unicode
from StringIO import StringIO


_, tag_, N_, add_domain = \
    domain_functions('navigationplugin', '_', 'tag_', 'N_', 'add_domain')

SESSION_KEY = 'display_navigation'
DISPLAY_CHOICES = ['normal', 'fixed_menu', 'buttom_ctx_menu']

class Navigation(Component):
    """This plugin enables user to choose, if she uses a different (means more
elegant way) display of naviagtion bar.

Type of displaying menu. Possible types are:
`normal` (default): No integration - ''leaves menu as in Trac standard'' 
`fixed_menu`: fixes menu on top of browser window,
`buttom_ctx_menu`: adds context menu at buttom of page, if available
"""
    implements(IRequestFilter, ITemplateProvider, ITemplateStreamFilter)

    display_navigation = ChoiceOption('trac', 'display_nav',
        choices=DISPLAY_CHOICES,
        doc="""Type of displaying menu. Possible types are:
`normal` (default): No integration - ''leaves menu as in Trac standard'' 
`fixed_menu`: fixes menu on top of browser window,
`buttom_ctx_menu`: adds context menu at buttom of page, if available""")
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
#        self.log.info("processing NavigationPlugin with option: %s" % self.display_navigation)
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
        self.log.info('display: %s' % display)
        if not display == 'normal':
            # non-standard"
            if 'fixed_menu' == display:
                return self._add_style_attributes(req, stream)
            elif 'buttom_ctx_menu' == display:
                return self._add_buttom_ctx_menu(req, stream)
        return stream

    
    def get_display(self, req):
        if req.args and req.args.has_key('action') \
        and req.args['action'] == 'save' \
        and req.args.has_key(SESSION_KEY):
            req.session[SESSION_KEY] = req.args[SESSION_KEY]
        
        if req.session.has_key(SESSION_KEY):
            return req.session[SESSION_KEY]
        return self.display_navigation
    
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
            height += 15
            stream |= Transformer('.//div[@id="mainnav"]').attr('style', 'top: %ipx' % height)
            height += 14
            stream |= Transformer('.//div[@id="ctxtnav"]').attr('style', 'top: %ipx' % height)
            height += 24
            stream |= Transformer('.//div[@id="content"]').attr('style', 'top: %ipx' % height)
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
