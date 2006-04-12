from trac.core import *
from tractags.api import DefaultTaggingSystem, ITaggingSystemProvider, TagEngine
from trac.wiki.api import IWikiChangeListener, IWikiSyntaxProvider
from trac.util import Markup
import re

class WikiTaggingSystem(DefaultTaggingSystem):
    """ Subclass of DefaultTaggingSystem that knows how to retrieve wiki page
        titles. """
    def __init__(self, env):
        DefaultTaggingSystem.__init__(self, env, 'wiki')

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

    def name_details(self, name):
        """ Return a tuple of (href, wikilink, title). eg. ("/ticket/1", "#1", "Broken links") """
        page, title = self.page_info(name)
        href = self.env.href.wiki(name)
        defaults = DefaultTaggingSystem.name_details(self, name)
        return defaults[0:2] + (title,)

class WikiTags(Component):
    """ Implement tags in the Wiki system, a tag:<tag> link resolver and
        correctly deletes tags from Wiki pages that are removed. """

    implements(ITaggingSystemProvider, IWikiChangeListener, IWikiSyntaxProvider)

    # ITaggingSystemProvider methods
    def get_tagspaces_provided(self):
        yield 'wiki'

    def get_tagging_system(self, tagspace):
        return WikiTaggingSystem(self.env)

    # IWikiChangeListener methods
    def wiki_page_added(self, page):
        TagEngine(self.env).flush_link_cache(page)

    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        TagEngine(self.env).flush_link_cache(page)

    def wiki_page_deleted(self, page):
        # No point having tags on a non-existent page.
        self.env.log.debug("Removing all tags from 'wiki:%s'" % page.name)
        engine = TagEngine(self.env)
        engine.tagspace.wiki.remove_all_tags(None, page.name)
        engine.flush_link_cache(page)

    def wiki_page_version_deleted(self, page):
        # Wiki tags are not versioned. If they were, we'd delete them here.
        TagEngine(self.env).flush_link_cache(page)

    # IWikiSyntaxProvider methods
    def get_wiki_syntax(self):
        return []

    def get_link_resolvers(self):
        yield ('tag', self._tag_formatter)

    def _tag_formatter(self, formatter, ns, target, label):
        if '?' in target:
            target, args = target.split('?')[0:2]
            args = '?' + args
        else:
            args = ''
        expression_space = self.config.getbool('tags', 'expression_space')
        href, title = TagEngine(self.env).get_tag_link(target,
                                          is_expression=expression_space)
        return Markup('<a href="%s%s" title="%s">%s</a>' % (href, args,
                                                            title, label))

