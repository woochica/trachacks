from trac.core import *
from trac.web.chrome import ITemplateProvider
from trac.wiki.api import WikiSystem
from webadmin.web_ui import IAdminPageProvider
from api import IWikitoPDFFormat

import re

class WikitoPDFAdmin(Component):
    """A plugin allowing the export of multiple wiki pages in a single file."""

    formats = ExtensionPoint(IWikitoPDFFormat)

    implements(ITemplateProvider, IAdminPageProvider)
    
    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
        
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return []

    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('WIKI_ADMIN'):
            yield ('general', 'General', 'wikitopdf', 'WikitoPDF')

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
            
            return formats[format]['provider'].process_wikitopdf(req, format, title, subject, rightpages, date, version, rightpages[0])
            
            req.redirect(req.href.admin(cat, page))
        
        req.hdf['wikitopdf.allpages'] = allpages
        leftpages = [x for x in allpages if x not in rightpages]
        leftpages.sort()
        req.hdf['wikitopdf.leftpages'] = leftpages
        req.hdf['wikitopdf.rightpages'] = rightpages
        req.hdf['wikitopdf.formats'] = formats
        req.hdf['wikitopdf.default_format'] = formats.iterkeys().next()

        return 'admin_wikitopdf.cs', None

