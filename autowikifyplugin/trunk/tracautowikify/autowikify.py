# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2007 Alec Thomas
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import re
from genshi.builder import tag
from trac.config import IntOption, ListOption
from trac.core import Component, implements
from trac.util import Markup, escape, sorted
from trac.util.compat import set
from trac.wiki.api import IWikiChangeListener, IWikiSyntaxProvider, WikiParser, WikiSystem


class AutoWikify(Component):
    """ Automatically create links for all known Wiki pages, even those that
    are not in CamelCase. """
    implements(IWikiChangeListener, IWikiSyntaxProvider)

    exclude = ListOption('autowikify', 'exclude', doc=
        """List of Wiki pages to exclude from auto-wikification.""")
    explicitly_wikify = ListOption('autowikify', 'explicitly_wikify', doc=
        """List of Wiki pages to always Wikify, regardless of size.""")
    minimum_length = IntOption('autowikify', 'minimum_length', 3,
        """Minimum length of wiki page name to perform auto-wikification on.""")

    page = set()
    pages_re = None

    def __init__(self):
        self._update_pages()
        self._update_pages_re()

    ### IWikiChangeListener methods

    def wiki_page_added(self, page):
        self.pages.add(page.name)
        self._update_pages_re()

    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        pass

    def wiki_page_deleted(self, page):
        if page.name in self.pages:
            self.pages.remove(page.name)
            self._update_pages_re()

    def wiki_page_renamed(self, page, old_name):
        self.pages.discard(old_name)
        self.pages.add(page.name)
        self._update_pages_re()

    def wiki_page_version_deleted(self, page):
        pass

    ### IWikiSyntaxProvider methods

    def get_wiki_syntax(self):
        yield (self.pages_re, self._page_formatter)

    def get_link_resolvers(self):
        return []

    ### Internal methods

    def _page_formatter(self, formatter, ns, match):
        page = match.group('autowiki')
        return tag.a(page, href=self.env.href.wiki(page), class_='wiki')

    def _update_pages(self):
        all_pages = set(WikiSystem(self.env).get_pages())
        self.pages = set([p for p in all_pages if len(p) >= self.minimum_length])
        self.pages.difference_update(self.exclude)
        explicitly_wikified = set([p.strip() for p in (self.explicitly_wikify or '') if p.strip()])
        self.pages.update(explicitly_wikified)

    def _update_pages_re(self):
        self.pages_re = r'!?\b(?P<autowiki>' + '|'.join([re.escape(page) for page in self.pages]) + r')\b'
        # Force an update of cached WikiParser.rules
        WikiParser(self.env)._compiled_rules = None
