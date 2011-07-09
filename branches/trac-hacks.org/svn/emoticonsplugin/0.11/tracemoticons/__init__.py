# -*- coding: utf-8 -*-
#
# Copyright (C) 2005 Christopher Lenz <cmlenz@gmx.de>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import re
from pkg_resources import resource_filename

from trac.core import *
from trac.util import escape
from trac.web.chrome import ITemplateProvider
from trac.wiki import IWikiSyntaxProvider

EMOTICONS = {
    ':/': 'annoyed.png', ':-/': 'annoyed.png',
    '8)': 'cool.png', '8-)': 'cool.png', 'B)': 'cool.png', 'B-)': 'cool.png',
    ':(': 'frown.png', ':-(': 'frown.png',
    ':D': 'happy.png', ':-D': 'happy.png',
    ':P': 'razz.png', ':-P': 'razz.png',
    ':)': 'smile.png', ':-)': 'smile.png',
    ':|': 'stoic.png', ':-|': 'stoic.png',
    ':O': 'suprised.png', ':o': 'suprised.png', ':-O': 'suprised.png',
    ':-o': 'suprised.png',
    ';)': 'wink.png', ';-)': 'wink.png'
}


class EmoticonsSupport(Component):
    """Provides support for graphical emoticons in wiki-formatted text."""

    implements(ITemplateProvider, IWikiSyntaxProvider)

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        """Return the directories containing static resources."""
        return [('emoticons', resource_filename(__name__, 'icons'))]

    def get_templates_dirs(self):
        return []

    # IWikiSyntaxProvider methods

    def get_wiki_syntax(self):
        """Replace textual patterns representing emoticons with the
        corresponding icon."""
        def _replace(formatter, namespace, match):
            src = self.env.href.chrome('emoticons', EMOTICONS[match.group(0)])
            return '<img src="%s" alt="%s" class="emoticon" width="18" ' \
                   'height="18" style="vertical-align: middle" />' % (
                   escape(src), escape(match.group(0)))
        pattern = '|'.join([re.escape(pattern) for pattern in EMOTICONS])
        yield '\b' + pattern + '\b', _replace

    def get_link_resolvers(self):
        return []
