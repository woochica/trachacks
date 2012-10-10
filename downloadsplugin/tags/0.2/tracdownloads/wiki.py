# -*- coding: utf-8 -*-

from trac.core import *
from trac.mimeview import Context
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
                # Create context.
                context = Context.from_request(formatter.req)('downloads-wiki')
                db = self.env.get_db_cnx()
                context.cursor = db.cursor()

                # Get API component.
                api = self.env[DownloadsApi]

                # Get download.
                if re.match(r'\d+', params): 
                    download = api.get_download(context, params)
                else:
                    download = api.get_download_by_file(context, params)

                if download:
                    # Return link to existing file.
                    return html.a(label, href = formatter.href.downloads(params),
                      title = '%s (%s)' % (download['file'],
                      pretty_size(download['size'])))
                else:
                    # Return link to non-existing file.
                    return html.a(label, href = '#', title = 'File not found.',
                      class_ = 'missing')
            else:
                # Return link to file to which is no permission. 
                return html.a(label, href = '#', title = 'No permission to file.',
                   class_ = 'missing')
