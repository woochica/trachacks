# -*- coding: utf8 -*-

import re

from tracscreenshots.api import *
from trac.core import *
from trac.wiki import IWikiSyntaxProvider
from trac.util.html import html

class ScreenshotsWiki(Component):
    """
        The wiki module implements macro for screenshots referencing.
    """
    implements(IWikiSyntaxProvider)

    # IWikiSyntaxProvider
    def get_link_resolvers(self):
        yield ('screenshot', self._screenshot_link)

    def get_wiki_syntax(self):
        return []

    # Internal functions

    def _screenshot_link(self, formatter, ns, params, label):
        if ns == 'screenshot':
            # Get database access.
            db = self.env.get_db_cnx()
            cursor = db.cursor()

            # Get API component.
            api = self.env[ScreenshotsApi]

            # Get macro values.
            match = re.match(r'''^(\d+)($|,(\d+)x(\d+)$)''', params)
            screenshot_id = int(match.group(1))
            screenshot_width = int(match.group(3) or 0)
            screenshot_height = int(match.group(4) or 0)
            self.log.debug('screenshot: %d %dx%d' % (screenshot_id,
              screenshot_width, screenshot_height))

            # Set original dimensions if zeros given.
            screenshot = api.get_screenshot(cursor, screenshot_id)
            if not screenshot_width:
                screenshot_width = screenshot['width']
            if not screenshot_height:
                screenshot_height = screenshot['height']

            # Return macro content
            if screenshot:
                if match.group(2):
                    image = html.img(src = formatter.href.screenshots(
                      screenshot['id'], width = screenshot_width,
                      height = screenshot_height), alt = screenshot['description'],
                      width = screenshot_width, height = screenshot_height)
                    return html.a(image, href = formatter.href.screenshots(
                      screenshot['id']), title = label)
                else:
                    return html.a(label, href = formatter.href.screenshots(
                      screenshot['id']), title = screenshot['description'])
            else:
                return html.a(label, href = formatter.href.screenshots(),
                  title = params, class_ = 'missing')
