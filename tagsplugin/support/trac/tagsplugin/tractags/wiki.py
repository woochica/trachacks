from trac.core import *
from tractags.api import DefaultTaggingSystem, ITaggingSystemProvider, TagEngine
from trac.wiki.api import IWikiChangeListener
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

    def name_details(self, tagspace, name):
        """ Return a tuple of (href, wikilink, title). eg. ("/ticket/1", "#1", "Broken links") """
        page, title = self.page_info(name)
        href = self.env.href.wiki(name)
        defaults = DefaultTaggingSystem.name_details(self, tagspace, name)
        return defaults[0:2] + (title,)

class WikiTags(Component):
    """ Implement tags in the Wiki system. """

    implements(ITaggingSystemProvider, IWikiChangeListener)

    tags_re = re.compile(r'''[^{]\s\[\[TagIt\(([0-9a-zA-Z,\/\. +-]*)\)\]\]''')

    # ITaggingSystemProvider methods
    def get_tagspaces_provided(self):
        yield 'wiki'

    def get_tagging_system(self, tagspace):
        return WikiTaggingSystem(self.env)

    # IWikiChangeListener methods
    def wiki_page_added(self, page):
        self._update_tags(page)

    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        self._update_tags(page)

    def wiki_page_deleted(self, page):
        self.env.log.debug("Removing all tags from 'wiki:%s'" % page.name)
        wiki_tags = TagEngine(self.env).wiki
        wiki_tags.remove_all_tags(None, page.name)

    def wiki_page_version_deleted(self, page):
        self.env.log.debug("Wiki page version deleted, updating tags")
        self._update_tags(page)

    # Internal methods
    def _update_tags(self, page):
        tags = self.tags_re.findall(page.text)
        if not tags: return
        tags = [t.strip() for t in tags[-1].split(',') if t.strip()]
        self.env.log.debug("Setting page tags for 'wiki:%s' to %s" % (page.name, tags))
        wiki_tags = TagEngine(self.env).wiki
        wiki_tags.replace_tags(None, page.name, *tags)
