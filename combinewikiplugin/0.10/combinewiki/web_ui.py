
# TracCombineWiki plugin
# Copyright 2006 Noah Kantrowitz

from trac.core import *
from trac.web.chrome import ITemplateProvider
from trac.wiki.api import WikiSystem

from webadmin.web_ui import IAdminPageProvider

import re

from api import ICombineWikiFormat

class CombineWikiModule(Component):
    """A plugin allowing the export of multiple wiki pages in a single file."""

    formats = ExtensionPoint(ICombineWikiFormat)

    implements(ITemplateProvider, IAdminPageProvider)
    
    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
        
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        #return [['combinewiki', resource_filename(__name__, 'htdocs'))]
        return []

    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('WIKI_ADMIN'):
            yield ('general', 'General', 'combinewiki', 'Combine Wiki')

    def process_admin_request(self, req, cat, page, path_info):
        allpages = list(WikiSystem(self.env).get_pages())
        rightpages = [x for x in req.session.get('combinewiki_rightpages', '').split(',') if x]

        formats = {}
        for provider in self.formats:
            for format, name in provider.combinewiki_formats(req):
                formats[format] = {
                    'name': name,
                    'provider': provider,
                }
        
        if req.method == 'POST':
            rightpages = req.args.get('rightpages_all')
            title = req.args.get('title') or self.env.project_name
            req.session['combinewiki_rightpages'] = rightpages
            rightpages = rightpages.split(',')
            format = req.args.get('format')
            if not format or format not in formats:
                raise TracError('Bad format given for CombineWiki output.')
            
            return formats[format]['provider'].process_combinewiki(req, format, title, rightpages)
            
            req.redirect(req.href.admin(cat, page))
        
        req.hdf['combinewiki.allpages'] = allpages
        leftpages = [x for x in allpages if x not in rightpages]
        leftpages.sort()
        req.hdf['combinewiki.leftpages'] = leftpages
        req.hdf['combinewiki.rightpages'] = rightpages
        req.hdf['combinewiki.formats'] = formats

        return 'combinewiki_admin.cs', None

