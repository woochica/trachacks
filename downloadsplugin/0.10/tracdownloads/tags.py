from tracdownloads.api import *
from trac.core import *
from tractags.api import ITaggingSystemProvider, DefaultTaggingSystem

class DownloadsTaggingSystem(DefaultTaggingSystem):
    """
      Tagging system which returns tags of all created downloads.
    """
    def __init__(self, env, component, req):
        self.component = component
        self.req = req
        DefaultTaggingSystem.__init__(self, env, 'downloads')

    def name_details(self, name):
        # Get cursor.
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # Get API object.
        api = DownloadsApi(self.component)

        # Return a tuple of (href, wikilink, title)
        defaults = DefaultTaggingSystem.name_details(self, name)
        return defaults

class DownloadsTags(Component):
    """
        The tags module implements plugin's ability to create tags related
        to downloads.
    """
    implements(ITaggingSystemProvider)

    # ITaggingSystemProvider methods.

    def get_tagspaces_provided(self):
        yield 'downloads'

    def get_tagging_system(self, tagspace):
        return DownloadsTaggingSystem(self.env, self, None)
