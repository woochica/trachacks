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

    # [screenshot] macro attributes regular expression.
    attributes_re = re.compile('(align|border|width|height|alt|title|longdesc|'
      'class|id|usemap)=(.+)')

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

            # Get macro arguments and screenshot.
            arguments = params.split(',')
            screenshot_id = int(arguments[0])
            screenshot = api.get_screenshot(cursor, screenshot_id)

            # Return macro content
            if screenshot:
                # Set default values of image attributes.
                attributes = {'alt' : screenshot['description']}

                # Fill attributes from macro arguments.
                for argument in arguments[1:]:
                    argument = argument.strip()
                    match = self.attributes_re.match(argument)
                    if match:
                        attributes[str(match.group(1))] = match.group(2)
                if attributes.has_key('width'):
                    if attributes['width'] == '0':
                        attributes['width'] = screenshot['width']
                if attributes.has_key('height'):
                    if attributes['height'] == '0':
                        attributes['height'] = screenshot['height']
                self.log.debug('attributes: %s' % (attributes,))

                # Build screenshot image and/or screenshot link.
                if attributes.has_key('width') and attributes.has_key('height'):
                    image = html.img(src = formatter.href.screenshots(
                      screenshot['id'], width = attributes['width'], height =
                      attributes['height'], format = 'raw'), **attributes)
                    return html.a(image, href = formatter.href.screenshots(
                      screenshot['id']), title = label)
                else:
                    return html.a(label, href = formatter.href.screenshots(
                      screenshot['id']), title = screenshot['description'])
            else:
                return html.a(label, href = formatter.href.screenshots(),
                  title = params, class_ = 'missing')
