""" Copyright (c) 2008 Martin Scharrer <martin@scharrer-online.de>
    $Id$
    $URL$

    This is Free Software under the BSD license.

    Contributors:
    Joshua Hoke <joshua.hoke@sixnet.com>: Patch for PageOutline Support (th:#4521)

    The regexes XML_NAME (unchanged) and NUM_HEADLINE (added 'n'-prefix for all
    names) were taken from trac.wiki.parser and the base code of method
    `_parse_heading` was taken from trac.wiki.formatter which are:
        Copyright (C) 2003-2008 Edgewall Software
        All rights reserved.
    See http://trac.edgewall.org/wiki/TracLicense for details.

"""
from genshi.builder import tag
from trac.core import *
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.wiki.api import IWikiSyntaxProvider
from trac.wiki.formatter import format_to_oneliner
from genshi.util import plaintext
from trac.wiki.parser import WikiParser

from weakref import WeakKeyDictionary
import re


class NumberedHeadlinesPlugin(Component):
    """ Trac Plug-in to provide Wiki Syntax and CSS file for numbered headlines.
    """
    implements(IRequestFilter,ITemplateProvider,IWikiSyntaxProvider)

    XML_NAME = r"[\w:](?<!\d)[\w:.-]*?" # See http://www.w3.org/TR/REC-xml/#id 

    NUM_HEADLINE = \
        r"(?P<nheading>^\s*(?P<nhdepth>#+)\s.*\s(?P=nhdepth)\s*" \
        r"(?P<nhanchor>=%s)?(?:\s|$))" % XML_NAME

    outline_counters = WeakKeyDictionary()

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('numberedheadlines', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []


    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        add_stylesheet (req, 'numberedheadlines/style.css')
        return (template, data, content_type)


    # IWikiSyntaxProvider methods
    def _parse_heading(self, formatter, match, fullmatch):
        shorten = False
        match = match.strip()

        depth = min(len(fullmatch.group('nhdepth')), 6)
        anchor = fullmatch.group('nhanchor') or ''
        heading_text = match[depth+1:-depth-1-len(anchor)]
        heading = format_to_oneliner(formatter.env, formatter.context, heading_text,
                                     False)
        if anchor:
            anchor = anchor[1:]
        else:
            sans_markup = plaintext(heading, keeplinebreaks=False)
            anchor = WikiParser._anchor_re.sub('', sans_markup)
            if not anchor or anchor[0].isdigit() or anchor[0] in '.-':
                # an ID must start with a Name-start character in XHTML
                anchor = 'a' + anchor # keeping 'a' for backward compat
        i = 1
        anchor_base = anchor
        while anchor in formatter._anchors:
            anchor = anchor_base + str(i)
            i += 1
        formatter._anchors[anchor] = True
        if shorten:
            heading = format_to_oneliner(formatter.env, formatter.context, heading_text,
                                         True)

        ## BEGIN of code provided by Joshua Hoke, see th:#4521.
        # Figure out headline numbering for outline
        counters = self.outline_counters.get(formatter, [])

        if formatter not in self.outline_counters:
            self.outline_counters[formatter] = counters

        if len(counters) < depth:
            delta = depth - len(counters)
            counters.extend([0] * (delta - 1))
            counters.append(1)
        else:
            del counters[depth:]
            counters[-1] += 1

        # Strip out link tags
        oheading = re.sub(r'</?a(?: .*?)?>', '', heading)
        # Add in number
        oheading = '.'.join(map(str, counters) + [" "]) + oheading

        try:
            # Add heading to outline
            formatter.outline.append((depth, anchor, oheading))
        except AttributeError:
            # Probably a type of formatter that doesn't build an
            # outline.
            pass
        ## END of provided code

        return tag.__getattr__('h' + str(depth))( heading,
                    class_='numbered',
                    id=anchor
               );

    def get_wiki_syntax(self):
        yield ( self.NUM_HEADLINE , self._parse_heading )

    def get_link_resolvers(self):
        return []

