# -*- coding: utf-8 -*-
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

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + ur"$Rev$"[6:-2])
__date__     = ur"$Date$"[7:-2]

from genshi.builder import tag
from trac.core import *
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.wiki.api import IWikiSyntaxProvider
from trac.wiki.formatter import format_to_oneliner
from genshi.util import plaintext
from trac.util import to_unicode
from trac.wiki.parser import WikiParser
from trac.config import BoolOption

from weakref import WeakKeyDictionary
import re

class NumberedHeadlinesPlugin(Component):
    """ Trac Plug-in to provide Wiki Syntax and CSS file for numbered headlines.
    """
    implements(IWikiSyntaxProvider)

    number_outline = BoolOption('numberedheadlines', 'numbered_outline', True,
        "Whether or not to number the headlines in an outline (e.g. TOC)")
    startatleveltwo = \
      BoolOption('numberedheadlines', 'numbering_starts_at_level_two',
        False, """Whether or not to start the numbering at level two instead at 
        level one.""")
    fix_paragraph = BoolOption('numberedheadlines', 'fix_paragraph', True, 'Fix surrounding paragraph HTML-tags.')

    XML_NAME = r"[\w:](?<!\d)[\w:.-]*?" # See http://www.w3.org/TR/REC-xml/#id 

    NUM_HEADLINE = \
        r"(?P<nheading>^\s*(?P<nhdepth>#+)\s" \
        r"(?P<nheadnum>\s*[0-9.]+\s)?.*\s(?P=nhdepth)\s*" \
        r"(?P<nhanchor>=%s)?(?:\s|$))" % XML_NAME

    outline_counters = WeakKeyDictionary()

    def _int(self,s):
      try:
        return int(s)
      except:
        return -1

    # IWikiSyntaxProvider methods
    def _parse_heading(self, formatter, match, fullmatch):
        shorten = False
        match = match.strip()

        depth = min(len(fullmatch.group('nhdepth')), 6)

        try:
          formatter.close_table()
          formatter.close_paragraph()
          formatter.close_indentation()
          formatter.close_list()
          formatter.close_def_list()
        except:
          pass

        ## BEGIN of code provided by Joshua Hoke, see th:#4521.
        # moved and modified by Martin

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
        ## END

        num    = fullmatch.group('nheadnum') or ''
        anchor = fullmatch.group('nhanchor') or ''
        heading_text = match[depth+1+len(num):-depth-1-len(anchor)].strip()

        num = num.strip()
        if num and num[-1] == '.':
          num = num[:-1]
        if num:
          numbers = [self._int(n) for n in num.split('.')]
          if len(numbers) == 1:
            counters[depth-1] = numbers[0]
          else:
            if len(numbers) > depth:
              del numbers[depth:]
            n = 0
            while numbers[n] == -1:
              n = n + 1
            counters[depth-len(numbers[n:]):] = numbers[n:]

        if not heading_text:
          return tag()

        heading = format_to_oneliner(formatter.env, formatter.context, 
            heading_text, False)

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

        # Add number directly if CSS is not used
        s = self.startatleveltwo and 1 or 0
        #self.env.log.debug('NHL:' + str(counters))
        while s < len(counters) and counters[s] == 0:
          s = s + 1

        oheading_text = heading_text
        heading_text = '.'.join(map(str, counters[s:]) + [" "]) + heading_text

        if self.number_outline:
          oheading_text = heading_text

        heading = format_to_oneliner(formatter.env, formatter.context, 
            heading_text, False)
        oheading = format_to_oneliner(formatter.env, formatter.context, 
            oheading_text, False)

        ## BEGIN of code provided by Joshua Hoke, see th:#4521.
        # modified by Martin

        # Strip out link tags
        oheading = re.sub(r'</?a(?: .*?)?>', '', oheading)

        try:
            # Add heading to outline
            formatter.outline.append((depth, anchor, oheading))
        except AttributeError:
            # Probably a type of formatter that doesn't build an
            # outline.
            pass
        ## END of provided code

        html = tag.__getattr__('h' + str(depth))(
            heading, id = anchor)
        if self.fix_paragraph:
          return '</p>' + to_unicode(html) + '<p>'
        else:
          return html

    def get_wiki_syntax(self):
        yield ( self.NUM_HEADLINE , self._parse_heading )

    def get_link_resolvers(self):
        return []

