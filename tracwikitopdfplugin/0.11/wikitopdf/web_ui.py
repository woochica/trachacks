"""
Copyright (C) 2008 Prognus Software Livre - www.prognus.com.br
Author: Diorgenes Felipe Grzesiuk <diorgenes@prognus.com.br>
"""

from trac.core import *
from trac.perm import IPermissionRequestor
from trac.web.chrome import ITemplateProvider, add_script
from trac.web.api import IRequestFilter
from trac.admin.web_ui import IAdminPanelProvider
from genshi.core import Markup
from api import IWikiToPdfFormat
from trac.wiki.api import WikiSystem
import urllib
import re

class WikiToPdfAdmin(Component):
    """A plugin allowing the export of multiple wiki pages in a single file."""

    formats = ExtensionPoint(IWikiToPdfFormat)

    implements(IPermissionRequestor, IAdminPanelProvider, ITemplateProvider, IRequestFilter)

    # IPermissionRequestor methods
    def get_permission_actions(self):
        return []

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
        
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('wikitopdf', resource_filename(__name__, 'htdocs'))]
        #return []

    # IAdminPanelsProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('WIKI_ADMIN'):
            yield ('general', 'General', 'wikitopdf', 'WikiToPdf')

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type	

    def process_admin_request(self, req, cat, page, path_info):
        allpages = list(WikiSystem(self.env).get_pages())
        rightpages = [x for x in req.session.get('wikitopdf_rightpages', '').split(',') if x]

        formats = {}
        for provider in self.formats:
            for format, name in provider.wikitopdf_formats(req):
                formats[format] = {
                    'name': name,
                    'provider': provider,
                }
        
        if req.method == 'POST':
            rightpages = req.args.get('rightpages_all')
            title = req.args.get('title').encode('latin-1') or self.env.project_name.encode('latin-1')
            subject = req.args.get('subject').encode('latin-1')
            date = req.args.get('date').encode('latin-1');
            version = req.args.get('version').encode('latin-1');
            toctitle = req.args.get('toctitle')
            req.session['wikitopdf_rightpages'] = rightpages
            rightpages = rightpages.split(',')
            format = req.args.get('format')

            if not format or format not in formats:
                raise TracError('Bad format given for WikiToPdf output.')

            pdfbookname = title 
 	    pdfbookname = pdfbookname.replace(' ', '') 
	    pdfbookname = pdfbookname.replace(':', '') 
	    pdfbookname = pdfbookname.replace(',', '') 

            return formats[format]['provider'].process_wikitopdf(req, format, title, subject, rightpages, date, version, pdfbookname)
            
            req.redirect(req.href.admin(cat, page))
        
        req.hdf['wikitopdf.allpages'] = allpages
        leftpages = [x for x in allpages if x not in rightpages]
        leftpages.sort()
        req.hdf['wikitopdf.leftpages'] = leftpages
        req.hdf['wikitopdf.rightpages'] = rightpages
        req.hdf['wikitopdf.formats'] = formats
        req.hdf['wikitopdf.default_format'] = formats.iterkeys().next()

        add_script(req, 'wikitopdf/js/admin_wikitopdf.js') 

        return 'admin_wikitopdf.cs', None

