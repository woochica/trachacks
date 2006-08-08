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
        # Get tagged screenshots.
        api = ScreenshotsApi(self.component, self.req)
        screenshot = api.get_screenshot(name)

        # Return a tuple of (href, wikilink, title)
        defaults = DefaultTaggingSystem.name_details(self, name)
        return (None, wiki_to_oneliner('[screenshot:%s %s]' % (screenshot['id'],
          screenshot['name']), self.env), screenshot['description'])

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
