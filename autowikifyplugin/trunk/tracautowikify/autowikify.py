# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2007 Alec Thomas
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import re
from genshi.builder import tag
from trac.config import IntOption, ListOption
from trac.core import Component, implements
from trac.util.compat import set
from trac.wiki.api import IWikiChangeListener, IWikiSyntaxProvider, WikiParser, WikiSystem


class AutoWikify(Component):
    """ Automatically create links for all known Wiki pages, even those that
    do not have CamelCase names. """
    implements(IWikiChangeListener, IWikiSyntaxProvider)

    exclude = ListOption('autowikify', 'exclude', doc=
        """List of Wiki pages to exclude from auto-wikification.""")
    explicitly_wikify = ListOption('autowikify', 'explicitly_wikify', doc=
        """List of Wiki pages to always Wikify, regardless of size.""")
    minimum_length = IntOption('autowikify', 'minimum_length', 3,
        """Minimum length of wiki page name to autowikify.""")

    pages = set()

    def __init__(self):
        self._update_pages()
        self._update_compiled_rules()

    ### IWikiChangeListener methods

    def wiki_page_added(self, page):
        self.pages.add(page.name)
        self._update_compiled_rules()

    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        pass

    def wiki_page_deleted(self, page):
        if page.name in self.pages:
            self.pages.remove(page.name)
            self._update_compiled_rules()

    def wiki_page_renamed(self, page, old_name):
        self.pages.discard(old_name)
        self.pages.add(page.name)
        self._update_compiled_rules()

    def wiki_page_version_deleted(self, page):
        pass

    ### IWikiSyntaxProvider methods

    def get_wiki_syntax(self):

        pages_re = r'!?\b(?P<autowiki>' + \
            '|'.join([re.escape(page) for page in self.pages]) + r')\b'

        def page_formatter(formatter, ns, match):
            page = match.group('autowiki')
            return tag.a(page, href=formatter.href.wiki(page), class_='wiki')

        yield (pages_re, page_formatter)

    def get_link_resolvers(self):
        return []

    ### Internal methods

    def _update_pages(self):
        all_pages = WikiSystem(self.env).get_pages()
        self.pages = set([p for p in all_pages if len(p) >= self.minimum_length])
        exclude = set([p.strip() for p in (self.exclude or '') if p.strip()])
        self.pages.difference_update(exclude)
        explicitly_wikified = set([p.strip() for p in (self.explicitly_wikify or '') if p.strip()])
        self.pages.update(explicitly_wikified)

    def _update_compiled_rules(self):
        # Force an update of cached WikiParser.rules
        WikiParser(self.env)._compiled_rules = None
