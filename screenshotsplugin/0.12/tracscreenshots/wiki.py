# -*- coding: utf-8 -*-

# Standard includes.
import re

# Trac includes.
from trac.core import *
from trac.config import Option
from trac.web.chrome import add_stylesheet, add_script, format_datetime
from trac.wiki.formatter import format_to_html, format_to_oneliner
from trac.util.html import html
from trac.util.text import to_unicode

# Trac interfaces.
from trac.wiki import IWikiSyntaxProvider, IWikiMacroProvider

# Local includes.
from tracscreenshots.api import *

class ScreenshotsWiki(Component):
    """
        The wiki module implements macro for screenshots referencing.
    """
    implements(IWikiSyntaxProvider, IWikiMacroProvider)

    # Configuration options.
    default_description = Option('screenshots', 'default_description',
      '$description', doc = 'Template for embended image description.')
    default_list_item = Option('screenshots', 'default_list_item', '$id - '
      '$name - $description',  doc = 'Default format of list item description '
      'of ![[ScreenshotsList()]] macro.')

    def __init__(self):
        self.screenshot_macro_doc = """Allows embed screenshot image in
wiki page. First mandatory argument is ID of the screenshot. Number or
image attributes can be specified next:

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
 * {{{$tags}}} - Comma separated list of screenshot tags.
 * {{{$components}}} - Comma separated list of screenshot components.
 * {{{$versions}}} - Comma separated list of screenshot versions.

Example:

{{{
 [[Screenshot(2,width=400,height=300,description=The $name by $author: $description,align=left)]]
}}}"""

        self.screenshots_list_macro_doc = """Displays list of all available
screenshots on wiki page. Accepts one argument which is template for
list items formatting. Possible variables in this template are:

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

        # [screenshot:<id>] macro id regular expression.
        self.id_re = re.compile('^(\d+)($|.+$)')

        # [[Screenshot()]] macro attributes regular expression.
        self.attributes_re = re.compile('(align|alt|border|class|description|'
          'format|height|id|longdesc|title|usemap|width)=(.*)')

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

    def expand_macro(self, formatter, name, content):

        # Create request context.
        context = Context.from_request(formatter.req)('screenshots-wiki')

        # Get database access.
        db = self.env.get_db_cnx()
        context.cursor = db.cursor()

        # Get API component.
        api = self.env[ScreenshotsApi]

        if name == 'Screenshot':
            # Check permission.
            if not formatter.req.perm.has_permission('SCREENSHOTS_VIEW'):
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
            screenshot = api.get_screenshot(context, screenshot_id)

            # Build and return macro content.
            if screenshot:
                # Set default values of image attributes.
                attributes = {'align' : 'none',
                              'border' : '1',
                              'format' : 'raw',
                              'alt' : screenshot['description'],
                              'description' : self.default_description}

                # Fill attributes from macro arguments.
                for argument in arguments[1:]:
                    argument = argument.strip()
                    match = self.attributes_re.match(argument)
                    if match:
                        attributes[str(match.group(1))] = match.group(2)

                # Zero width or height means keep original.
                if attributes.has_key('width'):
                    if attributes['width'] == 0:
                        attributes['width'] = screenshot['width']
                if attributes.has_key('height'):
                    if attributes['height'] == 0:
                        attributes['height'] = screenshot['height']

                # If one dimension is missing compute second to keep aspect.
                if not attributes.has_key('width') and \
                  attributes.has_key('height'):
                    attributes['width'] = int(int(attributes['height']) * (
                      float(screenshot['width']) / float(screenshot['height']))
                      + 0.5)
                if not attributes.has_key('height') and \
                  attributes.has_key('width'):
                    attributes['height'] = int(int(attributes['width']) * (
                      float(screenshot['height']) / float(screenshot['width']))
                      + 0.5)

                # If both dimensions are missing keep original.
                if not attributes.has_key('width') and not \
                  attributes.has_key('height'):
                    attributes['width'] = screenshot['width']
                    attributes['height'] = screenshot['height']

                self.log.debug('attributes: %s' % (attributes,))

                # Format screenshot description from template.
                attributes['description'] = self._format_description(context,
                  attributes['description'], screenshot)

                # Make copy of attributes for image tag.
                img_attributes = {}
                for attribute in attributes.keys():
                    if attribute not in ('align', 'border', 'description',
                      'format', 'width', 'height'):
                        img_attributes[attribute] = attributes[attribute]

                # Add CSS for image.
                add_stylesheet(formatter.req, 'screenshots/css/screenshots.css')

                # Build screenshot image and/or screenshot link.
                image = html.img(src = formatter.req.href.screenshots(
                  screenshot['id'], format = 'raw', width = attributes['width'],
                  height = attributes['height']), **img_attributes)
                link = html.a(image, href = formatter.req.href.screenshots(
                  screenshot['id'], format = attributes['format']), title =
                  screenshot['description'], style = 'border-width: %spx;' % (
                  attributes['border'],))
                width_and_border = int(attributes['width']) + 2 * \
                  int(attributes['border'])
                description = html.span(attributes['description'], class_ =
                  'description', style = "width: %spx;" % (width_and_border,))
                auxilary = html.span(link, description, class_ = 'aux',
                  style = "width: %spx;" % (width_and_border,))
                thumbnail_class = 'thumbnail' + ((attributes['align'] == 'left')
                  and '-left' or (attributes['align'] == 'right') and '-right'
                  or '')
                thumbnail = html.span(auxilary, class_ = thumbnail_class)
                return thumbnail
            else:
                return html.a(screenshot_id, href =
                  formatter.req.href.screenshots(), title = content,
                  class_ = 'missing')

        elif name == 'ScreenshotsList':
            # Check permission.
            if not formatter.req.perm.has_permission('SCREENSHOTS_VIEW'):
               return html.div('No permissions to see screenshots.',
               class_ = 'system-message')

            # Get desired list item description
            list_item_description = content or self.default_list_item

            # Get all screenshots.
            screenshots = api.get_screenshots_complete(context)

            # Create and return HTML list of screenshots.
            list_items = []
            for screenshot in screenshots:
                list_item = self._format_description(context,
                  list_item_description, screenshot)
                list_items.append(html.li(html.a(list_item, href =
                  formatter.req.href.screenshots(screenshot['id']))))
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

            # Create request context.
            context = Context.from_request(formatter.req)('screenshots-wiki')

            # Get database access.
            db = self.env.get_db_cnx()
            context.cursor = db.cursor()

            # Get API component.
            api = self.env[ScreenshotsApi]

            # Try to get screenshots of that ID.
            screenshot = api.get_screenshot(context, screenshot_id)

            # Return macro content
            if screenshot:
                return html.a(label, href = formatter.href.screenshots(
                  screenshot['id']) + arguments, title =
                  screenshot['description'])
            else:
                return html.a(screenshot_id, href = formatter.href.screenshots(),
                  title = params, class_ = 'missing')

    def _format_description(self, context, template, screenshot):
        description = template.replace('$id', to_unicode(screenshot['id']))
        description = description.replace('$name', screenshot['name'])
        description = description.replace('$file',
          to_unicode(screenshot['file']))
        description = description.replace('$time', format_datetime(to_datetime(
          screenshot['time'], utc)))
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

        return format_to_oneliner(self.env, context, description)

