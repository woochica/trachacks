# -*- coding: iso-8859-1 -*-
#
# Copyright (C) 2011 Mikael Relbe <mikael@relbe.se>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# Author: Mikael Relbe <mikael@relbe.se>

"""Highlight attentional phrases.

Typical attentional phrases are `FIXME` and `TODO`.

Any delimiter `():<>` adjacent to a phrase will not be presented. This makes it
possible to naturally write, for example, `FIXME:` in a wiki text, but view the
phrase highlighted without the colon (`:`) which would not look natural.

Activate this component to highlight this: FIXME
"""

from inspect import cleandoc

from pkg_resources import resource_filename

from genshi.builder import tag
from genshi.core import Markup

from trac.config import ListOption
from trac.core import implements, Component
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.wiki import IWikiSyntaxProvider, IWikiMacroProvider, format_to_html

from tracwikiextras.icons import Icons
from tracwikiextras.util import prepare_regexp, render_table


class Phrases(Component):
    """Highlight attentional phrases like `FIXME`.

    Phrases that are highlighted are defined in the `[wikiextras]` section in
    `trac.ini`. Use the `ShowPhrases` macro to show a list of currently defined
    phrases.
    """
    
    implements(IRequestFilter, ITemplateProvider, IWikiSyntaxProvider,
               IWikiMacroProvider)

    fixme_phrases = ListOption('wikiextras', 'fixme_phrases', 'BUG, FIXME',
                               doc=
        """A list of attentional phrases or single words, separated by comma
        (`,`) that will be highlighted to catch attention. Any delimiter
        `():<>` adjacent to a phrase will not be presented. (i.e. do not
        include any of these delimiters in this list). This makes it possible
        to naturally write, for example, `FIXME:` in a wiki text, but view the
        phrase highlighted without the colon (`:`) which would not look
        natural. Use the `ShowPhrases` macro to show a list of currently
        defined phrases.""")

    todo_phrases = ListOption('wikiextras', 'todo_phrases', 'REVIEW, TODO',
                              doc="Analogous to `FIXME`-phrases, but "
                                  "presentation is less eye-catching.")

    done_phrases = ListOption('wikiextras', 'done_phrases',
                              'DONE, DEBUGGED, FIXED, REVIEWED',
                              doc="Analogous to `FIXME`-phrases, but "
                                  "presentation is less eye-catching.")

    def __init__(self):
        self.text = {}
        #noinspection PyArgumentList
        shadow = '' if Icons(self.env).shadowless else 'shadow'
        html = '<span class="wikiextras %s phrase %s">%s</span>'
        for (style, phrases) in [('fixme', self.fixme_phrases), 
                                 ('todo', self.todo_phrases),
                                 ('done', self.done_phrases)]:
            for phrase in phrases:
                self.text[phrase] = html % (shadow, style, phrase)
                self.text['!%s' % phrase] = phrase
                for (d1, d2) in [(':', ':'), ('<', '>'), ('(', ')')]:
                    wiki = '%s%s%s' % (d1, phrase, d2)
                    self.text[wiki] = html % (shadow, style, phrase)
                    self.text['!%s' % wiki] = wiki
                for d2 in [':']:
                    wiki = '%s%s' % (phrase, d2)
                    self.text[wiki] = html % (shadow, style, phrase)
                    self.text['!%s' % wiki] = wiki

    # IRequestFilter methods

    #noinspection PyUnusedLocal
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        add_stylesheet(req, 'wikiextras/css/phrases.css')
        return template, data, content_type

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return [('wikiextras', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

    # IWikiSyntaxProvider methods

    def get_wiki_syntax(self):
        yield (prepare_regexp(self.text), self._format_phrase)

    def get_link_resolvers(self):
        return []

    #noinspection PyUnusedLocal
    def _format_phrase(self, formatter, match, fullmatch):
        return Markup(self.text[match])

    # IWikiMacroProvider methods

    def get_macros(self):
        yield 'ShowPhrases'

    #noinspection PyUnusedLocal
    def get_macro_description(self, name):
        return cleandoc("""Renders in a table the list of known phrases that
                are highlighted to catch attention.

                Comment: Any delimiter `():<>` adjacent to a phrase will not be
                presented. This makes it possible to naturally write `FIXME:`,
                for example, but view the phrase highlighted without the colon
                (`:`) which would not look natural. Prefixing a phrase with `!`
                prevents it from being highlighted.
                """)

    #noinspection PyUnusedLocal
    def expand_macro(self, formatter, name, content, args=None):
        t = [render_table(p, '1',
                          lambda s: self._format_phrase(formatter, s, None))
             for p in [self.fixme_phrases, self.todo_phrases,
                       self.done_phrases]]
        style = 'border:none;text-align:center;vertical-align:top'
        spacer = tag.td(style='width:2em;border:none')
        return tag.table(tag.tr(tag.td(t[0], style=style), spacer,
                                tag.td(t[1], style=style), spacer,
                                tag.td(t[2], style=style)))


class AboutWikiPhrases(Component):
    """Macro for displaying a wiki page on how to use attentional phrases.

    Create a wiki page `WikiPhrases` and insert the following line to show
    detailed instructions to wiki authors on how to use attentional phrases
    in wiki pages:
    {{{
    [[AboutWikiPhrases]]
    }}}
    """

    implements(IWikiMacroProvider)

    # IWikiMacroProvider methods

    def get_macros(self):
        yield 'AboutWikiPhrases'

    #noinspection PyUnusedLocal
    def get_macro_description(self, name):
        return "Display a wiki page on how to use attentional phrases."

    #noinspection PyUnusedLocal
    def expand_macro(self, formatter, name, content, args=None):
        help_file = resource_filename(__name__, 'doc/WikiPhrases')
        fd = open(help_file, 'r')
        wiki_text = fd.read()
        fd.close()
        return format_to_html(self.env, formatter.context, wiki_text)
