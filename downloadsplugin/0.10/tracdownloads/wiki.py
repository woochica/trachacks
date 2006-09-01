from tracdownloads.api import *
from trac.core import *
from trac.wiki import IWikiSyntaxProvider
from trac.util.html import html

class DownloadsWiki(Component):
    """
        The wiki module implements macro for screenshots referencing.
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
            # Get cursor.
            db = self.env.get_db_cnx()
            cursor = db.cursor()

            # Get referenced screenshot.
            api = DownloadsApi(self)

            return html.a(label, href = formatter.href.downloads(),
              title = params, class_ = 'missing')
