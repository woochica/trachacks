# -*- coding: utf-8 -*-

from trac.core import *
from trac.util.html import html

from trac.wiki import IWikiSyntaxProvider

from tracdownloads.api import *

class DownloadsWiki(Component):
    """
        The wiki module implements macro for downloads referencing.
    """
    implements(IWikiSyntaxProvider)

    # IWikiSyntaxProvider
    def get_link_resolvers(self):
        yield ('download', self._download_link)

    def get_wiki_syntax(self):
        return []

    # Internal functions

    def _download_link(self, formatter, ns, params, label):
        if ns == 'download':
            if formatter.req.perm.has_permission('DOWNLOADS_VIEW'):
                # Get cursor.
                db = self.env.get_db_cnx()
                cursor = db.cursor()

                # Get API component.
                api = self.env[DownloadsApi]

                # Get download.
                download = api.get_download(cursor, params)

                if download:
                    # Return link to existing file.
                    return html.a(label, href = formatter.href.downloads(params),
                      title = download['file'])
                else:
                    # Return link to non-existing file.
                    return html.a(label, href = '#', title = 'File not found.',
                      class_ = 'missing')
            else:
                # Return link to file to which is no permission. 
                return html.a(label, href = '#', title = 'No permission to file.',
                   class_ = 'missing')
