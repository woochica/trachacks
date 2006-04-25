"""
$Id$
$HeadURL$

Copyright (c) 2006 Peter Kropf. All rights reserved.

Module documentation goes here.
"""



__revision__  = '$LastChangedRevision$'
__id__        = '$Id$'
__headurl__   = '$HeadURL$'
__docformat__ = 'restructuredtext'
__version__   = '0.1.0'


import fnmatch
from trac.core import *
from trac.web.main import IRequestHandler
from trac.web.chrome import ITemplateProvider
from trac.util import escape, Markup
from trac.wiki import IWikiSyntaxProvider


class PageListModule(Component):
    implements(IRequestHandler, ITemplateProvider, IWikiSyntaxProvider)


    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/pagelist')
    

    def process_request(self, req):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        pieces = [item for item in req.path_info.split('/pagelist') if len(item)]

        if len(pieces):
            pieces = [item for item in pieces[0].split('/') if len(item)]

            prefix = '*'
            suffix = '*'
            if len(pieces) > 1:
                if 'prefix' in pieces:
                    suffix = '*'
                    prefix = ''
                    pieces.remove('prefix')
                if 'suffix' in pieces:
                    suffix = ''
                    prefix = '*'
                    pieces.remove('suffix')

            if len(pieces):
                text = pieces[0]
            else:
                text = ''

            req.hdf['pagelist.pages'] = self._get_pagelist(cursor, '%s%s%s' % (prefix, text, suffix))
        return 'pagelist.cs', None


    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]


    # IWikiSyntaxProvider
    def get_link_resolvers(self):
        yield ('pagelist', self._pagelist_link)


    def get_wiki_syntax(self):
        return []


    # workers
    def _pagelist_link(self, formatter, ns, params, label):
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        prefix = '*'
        suffix = '*'
        pieces = params.split(':')
        if len(pieces) > 1:
            if 'prefix' in pieces:
                suffix = '*'
                prefix = ''
                pieces.remove('prefix')
            if 'suffix' in pieces:
                suffix = ''
                prefix = '*'
                pieces.remove('suffix')
        text = pieces[0]

        pagelist = [n['link'] for n in self._get_pagelist(cursor, '%s%s%s' % (prefix, text, suffix))]
        links = '<br/>'.join(pagelist)

        return links


    def _get_pagelist(self, cursor, pattern):
        cursor.execute('SELECT DISTINCT name FROM wiki ORDER BY name')
        link = '<a href="%s/%s">%s</a>'
        wiki = self.env.href.wiki()
        pagelist = [{'name': row[0],
                     'link': link % (wiki, row[0], row[0]),
                     'prefix': wiki,
                     }
                    for row in self._match_pages(pattern, cursor)]
        return pagelist


    def _match_pages(self, pattern, cursor):
        for row in cursor.fetchall():
            if fnmatch.fnmatch(row[0], pattern):
                yield row
            else:
                pass
