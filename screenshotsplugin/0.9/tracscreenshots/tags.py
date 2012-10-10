# -*- coding: utf-8 -*-

from tracscreenshots.api import *
from trac.core import *
from tractags.api import ITaggingSystemProvider, DefaultTaggingSystem

class ScreenshotsTaggingSystem(DefaultTaggingSystem):
    """
      Tagging system which returns tags of all created screenshots.
    """
    def __init__(self, env, component, req):
        self.component = component
        self.req = req
        DefaultTaggingSystem.__init__(self, env, 'screenshots')

    def name_details(self, name):
        # Get cursor.
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # Get tagged screenshots.
        api = ScreenshotsApi(self.component)
        screenshot = api.get_screenshot(cursor, name)

        # Return a tuple of (href, wikilink, title)
        defaults = DefaultTaggingSystem.name_details(self, name)
        if screenshot:
            return (defaults[0], wiki_to_oneliner('[screenshot:%s %s]' %
              (screenshot['id'], screenshot['name']), self.env),
              screenshot['description'])
        else:
            return defaults

class ScreenshotsTags(Component):
    """
        The tags module implements plugin's ability to create tags related
        to screenshots.
    """
    implements(ITaggingSystemProvider)

    # ITaggingSystemProvider methods.

    def get_tagspaces_provided(self):
        yield 'screenshots'

    def get_tagging_system(self, tagspace):
        return ScreenshotsTaggingSystem(self.env, self, None)
