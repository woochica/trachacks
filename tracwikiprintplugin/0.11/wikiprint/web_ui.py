"""
Copyright (C) 2008 Prognus Software Livre - www.prognus.com.br
Author: Diorgenes Felipe Grzesiuk <diorgenes@prognus.com.br>
Modified by: Alvaro Iradier <alvaro.iradier@polartech.es>
"""

from trac.core import *
from trac.perm import IPermissionRequestor
from trac.web.chrome import ITemplateProvider, add_script, add_notice, add_warning
from trac.admin.web_ui import IAdminPanelProvider
from genshi.core import Markup
from api import IWikiPrintFormat
from trac.wiki.api import WikiSystem
from trac.web.api import RequestDone
import wikiprint
import urllib
import re
import defaults

import ho.pisa as pisa

class WikiPrintAdmin(Component):
    """A plugin allowing the export of multiple wiki pages in a single file."""

    formats = ExtensionPoint(IWikiPrintFormat)

    implements(IPermissionRequestor, IAdminPanelProvider, ITemplateProvider)

    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ['WIKIPRINT_ADMIN', 'WIKIPRINT_FILESYSTEM', 'WIKIPRINT_BOOK']

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
        
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('wikiprint', resource_filename(__name__, 'htdocs'))]

    # IAdminPanelsProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('WIKIPRINT_ADMIN'):
            yield ('wikiprint', 'WikiPrint', 'options', 'Options')
            yield ('wikiprint', 'WikiPrint', 'makebook', 'Make Book')

    # IAdminPanelProvider methods
    def render_admin_panel(self, req, cat, page, component):
        
        if page == 'makebook':
            return self._render_book(req, cat, page, component)
        if page == 'options':
            return self._render_options(req, cat, page, component)
                
    
    def _render_book(self, req, cat, page, component):    
        req.perm.assert_permission('WIKIPRINT_BOOK')
        data = {}
        
        allpages = list(WikiSystem(self.env).get_pages())
        rightpages = [x for x in req.session.get('wikiprint_rightpages', '').split(',') if x]

        formats = {}
        for provider in self.formats:
            for format, name in provider.wikiprint_formats(req):
                formats[format] = {
                    'name': name,
                    'provider': provider,
                }
        
        if req.method == 'POST' and req.args.get('create'):
            rightpages = req.args.get('rightpages_all')
            title = req.args.get('title') or self.env.project_name
            subject = req.args.get('subject')
            date = req.args.get('date')
            version = req.args.get('version')
            format = req.args.get('format')

            req.session['wikiprint_rightpages'] = rightpages
            rightpages = rightpages.split(',')

            if not format or format not in formats:
                raise TracError('Bad format given for WikiPrint output.')
                
            pdfbookname = title.replace(' ', '_').replace(':', '_').replace(',', '_')
            return formats[format]['provider'].process_wikiprint(req, format, title, subject, rightpages, version, date, pdfbookname)
            
        data['allpages'] = allpages
        leftpages = [x for x in allpages if x not in rightpages]
        leftpages.sort()
        data['leftpages'] = leftpages
        data['rightpages'] = rightpages
        data['formats'] = formats
        data['default_format'] = formats.iterkeys().next()

        add_script(req, 'wikiprint/js/admin_wikiprint.js') 
        
        return 'admin_wikibook.html', data
    
    
    def _render_options(self, req, cat, page, component):    
        req.perm.assert_permission('WIKIPRINT_ADMIN')
        data = {}
        
        if req.method == 'POST' and req.args.get('saveurls'):
            self.env.config.set('wikiprint', 'css_url', req.args.get('css_url'))
            self.env.config.set('wikiprint', 'article_css_url', req.args.get('article_css_url'))
            self.env.config.set('wikiprint', 'book_css_url', req.args.get('book_css_url'))
            self.env.config.set('wikiprint', 'frontpage_url', req.args.get('frontpage_url'))
            self.env.config.set('wikiprint', 'extracontent_url', req.args.get('extracontent_url'))
            add_notice(req, "URLs saved")
            self.env.config.save()
        elif req.method == 'POST' and req.args.get('savehttpauth'):
            self.env.config.set('wikiprint', 'httpauth_user', req.args.get('httpauth_user'))
            self.env.config.set('wikiprint', 'httpauth_password', req.args.get('httpauth_password'))
            add_notice(req, "User and password saved")
            self.env.config.save()
        elif req.method == 'POST' and req.args.get('viewcss'):
            self.env.log.debug("Wikiprint, Viewing CSS")
            return self._send_resource_file(req, 'text/css', req.args.get('css_url'), defaults.CSS)
        elif req.method == 'POST' and req.args.get('viewbookcss'):
            self.env.log.debug("Wikiprint, Viewing Book CSS")
            return self._send_resource_file(req, 'text/css', req.args.get('book_css_url'), defaults.BOOK_EXTRA_CSS)
        elif req.method == 'POST' and req.args.get('viewarticlecss'):
            self.env.log.debug("Wikiprint, Viewing Article CSS")
            return self._send_resource_file(req, 'text/css', req.args.get('article_css_url'), defaults.ARTICLE_EXTRA_CSS)
        elif req.method == 'POST' and req.args.get('viewfrontpage'):
            self.env.log.debug("Wikiprint, Viewing Front page")
            return self._send_resource_file(req, 'text/html', req.args.get('frontpage_url'), defaults.FRONTPAGE)
        elif req.method == 'POST' and req.args.get('viewextracontent'):
            self.env.log.debug("Wikiprint, Viewing Extra Contents")
            return self._send_resource_file(req, 'text/html', req.args.get('extracontent_url'), defaults.EXTRA_CONTENT)
        
        data['css_url'] = self.env.config.get('wikiprint', 'css_url')
        data['article_css_url'] = self.env.config.get('wikiprint', 'article_css_url')
        data['book_css_url'] = self.env.config.get('wikiprint', 'book_css_url')
        data['frontpage_url'] = self.env.config.get('wikiprint', 'frontpage_url')
        data['extracontent_url'] = self.env.config.get('wikiprint', 'extracontent_url')
        

        data['httpauth_user'] = self.env.config.get('wikiprint', 'httpauth_user')
        data['httpauth_password'] = self.env.config.get('wikiprint', 'httpauth_password')

        return 'admin_wikiprint.html', data


    def _send_resource_file(self, req, content_type, file, default_value):
        # Send the output
        req.send_response(200)
        req.send_header('Content-Type', 'text/plain')
        if not file:
            out = default_value
        else:
            linkloader = wikiprint.linkLoader(self.env, req, allow_local = True)
            resolved_file = linkloader.getFileName(file)
            if not resolved_file :
                raise Exception("File or URL load problem: %s (need WIKIPRINT_FILESYSTEM permissions?)" % file)
            try:
                f = open(resolved_file)
                out = f.read()
                f.close()
            except IOError:
                raise Exception("File or URL load problem: %s (IO Error)" % file)
            del linkloader
            
        req.send_header('Content-Length', len(out))
        req.end_headers()
        req.write(out)
        raise RequestDone