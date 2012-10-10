# -*- coding: utf-8 -*-

import re

from trac.core import *
from trac.config import Option
from trac.wiki import wiki_to_html, wiki_to_oneliner
from trac.web.chrome import add_stylesheet, add_script
from trac.util.html import html
from trac.util.text import to_unicode
from trac.util.datefmt import format_datetime

from trac.wiki import IWikiSyntaxProvider, IWikiMacroProvider

from tracscreenshots.api import *

class ScreenshotsWiki(Component):

    screenshot_macro_doc = """Allows embed screenshot image in wiki page.
First mandatory argument is ID of the screenshot. Number or image attributes
can be specified next:

 * {{{align}}} - Specifies image alignment in wiki page. Possible values are:
   {{{left}}}, {{{right}}} and {{{center}}}.
 * {{{alt}}} - Alternative description of image.
 * {{{border}}} - Sets image border of specified width in pixels.
 * {{{class}}} - Class of image for CSS styling.
 * {{{description}}} - Brief description under the image. Accepts several
   variables (see bellow).
 * {{{format}}} - Format of returned image or screenshot behind link.
 * {{{height}}} - Height of image. Set to 0 if you want original image height.
 * {{{id}}} - ID of image for CSS styling.
 * {{{longdesc}}} - Detailed description of image.
 * {{{title}}} - Title of image.
 * {{{usemap}}} - Image map for clickable images.
 * {{{width}}} - Width of image. Set to 0 if you want original image width.

Attribute {{{description}}} displays several variables:

 * {{{$id}}} - ID of image.
 * {{{$name}}} - Name of image.
 * {{{$author}}} - User name who uploaded image.
 * {{{$time}}} - Time when image was uploaded.
 * {{{$file}}} - File name of image.
 * {{{$description}}} - Detailed description of image.
 * {{{$width}}} - Original width of image.
 * {{{$height}}} - Original height of image.

Example:

{{{
 [[Screenshot(2,width=400,height=300,description=The $name by $author: $description,align=left)]]
}}}"""

    screenshots_list_macro_doc = """Displays list of all available screenshots
on wiki page. Accepts one argument which is template for list items fromatting.
Possible variables in this template are:

 * {{{$id}}} - ID of image.
 * {{{$name}}} - Name of image.
 * {{{$author}}} - User name who uploaded image.
 * {{{$time}}} - Time when image was uploaded.
 * {{{$file}}} - File name of image.
 * {{{$description}}} - Detailed description of image.
 * {{{$width}}} - Original width of image.
 * {{{$height}}} - Original height of image.
 * {{{$tags}}} - Comma separated list of screenshot tags.
 * {{{$components}}} - Comma separated list of screenshot components.
 * {{{$versions}}} - Comma separated list of screenshot versions.

Example:

{{{
 [[ScreenshotsList($name - $description ($widthx$height))]]
}}}"""

    """
        The wiki module implements macro for screenshots referencing.
    """
    implements(IWikiSyntaxProvider, IWikiMacroProvider)

    # [screenshot] macro id regular expression.
    id_re = re.compile('^(\d+)($|.+$)')

    # [[Screenshot()]] macro attributes regular expression.
    attributes_re = re.compile('(align|alt|border|class|description|format|' \
      'height|id|longdesc|title|usemap|width)=(.*)')

    # Configuration options.
    default_description = Option('screenshots', 'default_description',
      '$description', 'Template for embended image description.')
    default_list_item = Option('screenshots', 'default_list_item', '$id - $name - $description',
      doc = 'Default format of list item description of [[ScreenshotsList()]]' \
      ' macro.')

    # IWikiSyntaxProvider

    def get_link_resolvers(self):
        yield ('screenshot', self._screenshot_link)

    def get_wiki_syntax(self):
        return []

    # IWikiMacroProvider

    def get_macros(self):
        yield 'Screenshot'
        yield 'ScreenshotsList'

    def get_macro_description(self, name):
        if name == 'Screenshot':
            return self.screenshot_macro_doc
        elif name == 'ScreenshotsList':
            return self.screenshots_list_macro_doc


    def render_macro(self, req, name, content):

        # Get database access.
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # Get API component.
        api = self.env[ScreenshotsApi]

        if name == 'Screenshot':
            # Check permission.
            if not req.perm.has_permission('SCREENSHOTS_VIEW'):
               return html.div('No permissions to see screenshots.',
               class_ = 'system-message')

            # Get macro arguments.
            arguments = content.split(',')

            # Get screenshot ID.
            try:
               screenshot_id = int(arguments[0])
            except:
                 raise TracError("Missing screenshot ID in macro arguments.")

            # Try to get screenshots of that ID.
            screenshot = api.get_screenshot(cursor, screenshot_id)

            # Build and return macro content.
            if screenshot:
                # Set default values of image attributes.
                attributes = {'align' : 'none',
                              'border' : '1',
                              'format' : 'raw',
                              'width' : screenshot['width'],
                              'height' : screenshot['height'],
                              'alt' : screenshot['description'],
                              'description' : self.default_description}

                # Fill attributes from macro arguments.
                for argument in arguments[1:]:
                    argument = argument.strip()
                    match = self.attributes_re.match(argument)
                    if match:
                        attributes[str(match.group(1))] = match.group(2)
                self.log.debug('attributes: %s' % (attributes,))

                # Format screenshot description from template.
                attributes['description'] = self._format_description(
                  attributes['description'], screenshot)

                # Make copy of attributes for image tag.
                img_attributes = {'align' : 'center',
                                  'style' : 'border-width: %spx;' % (
                                    attributes['border'],)}
                for attribute in attributes.keys():
                    if attribute not in ('align', 'border', 'description',
                      'format'):
                        img_attributes[attribute] = attributes[attribute]

                # Add CSS for image.
                add_stylesheet(req, 'screenshots/css/screenshots.css')

                # Build screenshot image and/or screenshot link.
                image = html.img(src = req.href.screenshots(screenshot['id'],
                  width = attributes['width'], height = attributes['height'],
                  format = 'raw'), **img_attributes)
                link = html.a(image, href = req.href.screenshots(screenshot['id'],
                  format = attributes['format']), title =
                  screenshot['description'])
                description = html.span(attributes['description'], class_ =
                  'description')
                thumbnail_class = 'thumbnail' + ((attributes['align'] == 'left')
                  and '-left' or (attributes['align'] == 'right') and '-right'
                  or '')
                thumbnail = html.span(link, ' ', description, class_ =
                  thumbnail_class, style = "width: %spx;" % (
                  int(attributes['width']) + 2 * int(attributes['border'],)))
                return thumbnail
            else:
                return html.a(screenshot_id, href = req.href.screenshots(),
                  title = content, class_ = 'missing')

        elif name == 'ScreenshotsList':
            # Check permission.
            if not req.perm.has_permission('SCREENSHOTS_VIEW'):
               return html.div('No permissions to see screenshots.',
               class_ = 'system-message')

            # Get desired list item description
            list_item_description = content or self.default_list_item

            # Get all screenshots.
            screenshots = api.get_screenshots_complete(cursor)

            # Create and return HTML list of screenshots.
            list_items = []
            for screenshot in screenshots:
                list_item = self._format_description(list_item_description,
                  screenshot)
                list_items.append(html.li(html.a(list_item, href =
                  req.href.screenshots(screenshot['id']))))
            return html.ul(list_items)

    # Internal functions

    def _screenshot_link(self, formatter, ns, params, label):
        if ns == 'screenshot':
            # Get screenshot ID and link arguments from macro.
            match = self.id_re.match(params)
            if match:
                screenshot_id = int(match.group(1))
                arguments = match.group(2)
            else:
                # Bad format of link.
                return html.a(label, href = formatter.href.screenshots(),
                  title = params, class_ = 'missing')

            # Get database access.
            db = self.env.get_db_cnx()
            cursor = db.cursor()

            # Get API component.
            api = self.env[ScreenshotsApi]

            # Try to get screenshots of that ID.
            screenshot = api.get_screenshot(cursor, screenshot_id)

            self.log.debug((params, label, arguments))

            # Return macro content
            if screenshot:
                return html.a(label, href = formatter.href.screenshots(
                  screenshot['id']) + arguments, title =
                  screenshot['description'])
            else:
                return html.a(screenshot_id, href =
                  formatter.href.screenshots(), title = params, class_ =
                  'missing')

    def _format_description(self, template, screenshot):
        description = template.replace('$id', to_unicode(screenshot['id']))
        description = description.replace('$name', screenshot['name'])
        description = description.replace('$file',
          to_unicode(screenshot['file']))
        description = description.replace('$time', format_datetime(
          screenshot['time']))
        description = description.replace('$author', screenshot['author'])
        description = description.replace('$description',
          screenshot['description'])
        description = description.replace('$width', to_unicode(
          screenshot['width']))
        description = description.replace('$height', to_unicode(
          screenshot['height']))
        description = description.replace('$tags', to_unicode(
          screenshot['tags']))
        description = description.replace('$components',
          ', '.join(screenshot['components']))
        description = description.replace('$versions',
          ', '.join(screenshot['versions']))
        return wiki_to_oneliner(description, self.env)

