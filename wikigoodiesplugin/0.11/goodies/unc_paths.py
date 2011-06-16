# -*- coding: iso-8859-1 -*-
#
# Copyright (C) 2006 Christian Boos <cboos@neuf.fr>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# Author: Christian Boos <cboos@neuf.fr>

from genshi.builder import tag

from trac.core import implements, Component
from trac.wiki import IWikiSyntaxProvider


class UNCPathLink(Component):

    implements(IWikiSyntaxProvider)

    # IWikiSyntaxProvider methods

    _unc_path_regexp = (
        r'!?(?:\\\\[^\s\\\\/]+(?:[\\/][^\s\\]*)+' # \\host\share[\path]
        r'|"\\\\[^"\s\\\\/]+(?:[\\/][^"\\]*)+"' # "\\host\share[\path ...]"
        r'|<\\\\[^>\s\\\\/]+(?:[\\/][^>\\]*)+>' # <\\host\share[\path ...]>
        r'|\[(?P<unc_path>\\\\[^\s\\\\/]+(?:[\\/][^\s\\]*)+)'
        r'(?P<unc_label>\s+[^]]+)?\]' # [\\host\share\path label]
        r')')

    def get_wiki_syntax(self):
        def filelink(formatter, match, fullmatch):
            label = None
            if match[0] == '[':
                match, label = (fullmatch.group('unc_path'),
                                fullmatch.group('unc_label'))
            elif match[0] in '"<':
                match = match[1:-1]
            return tag.a(label or match,
                         href='file:///' + match.replace('\\', '/'))
        yield (self._unc_path_regexp, filelink)

    def get_link_resolvers(self):
        def filelink(formatter, ns, target, label):
            return tag.a(label or target,
                         href='file:///' + target.replace('\\', '/'))           
        yield ('unc', filelink)
