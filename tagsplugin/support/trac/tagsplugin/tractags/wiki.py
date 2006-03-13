from trac.core import *
from tractags.api import DefaultTaggingSystem, ITaggingSystemProvider
import re

class WikiTaggingSystem(DefaultTaggingSystem):
    """ Subclass of DefaultTaggingSystem that knows how to retrieve wiki page
        titles. """
    def page_info(self, page):
        from trac.wiki import model
        """ Return tuple of (model.WikiPage, title) """
        page = model.WikiPage(self.env, page)

        title = ''

        if page.exists:
            text = page.text
            ret = re.search('=\s+([^=]*)=',text)
            title = ret and ret.group(1) or ''

        return (page, title)

    def name_link(self, tagspace, name):
        """ Return a tuple of (href, wikilink, title). eg. ("/ticket/1", "#1", "Broken links") """
        page, title = self.page_info(name)
        return (self.env.href.wiki(name), '[wiki:%s %s]' % (name, name), title)

class WikiTags(Component):
    """ Implement tags in the Wiki system. """

    implements(ITaggingSystemProvider)

    def get_tagspaces_provided(self):
        yield 'wiki'

    def get_tagging_system(self, tagspace):
        return WikiTaggingSystem(self.env)

