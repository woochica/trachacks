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

"""Use boxes to give wiki pages a modern look.
"""
import os

from inspect import cleandoc

from pkg_resources import resource_filename

from genshi.builder import tag

from trac.config import BoolOption, IntOption
from trac.core import implements, Component
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.wiki import IWikiMacroProvider, format_to_html, parse_args

from tracwikiextras.icons import Icons


# Urgency levels
WARN = 0
HIGHLIGHT = 1
ELABORATE = 2
NEWS = 3
NORMAL = 4


class Boxes(Component):
    """WikiProcessors for inserting boxes in a wiki page.

    Four processors are defined for creating boxes:
     * `box` -- The core box processor.
     * `rbox` -- Display a right aligned box to show side notes and warnings
       etc. This will probably be the most used box.
     * `newsbox` -- Display news in a right aligned box. ''(This box
       corresponds to the well-known ''`NewsFlash`'' macro.)''
     * `imagebox` -- Display a single image with caption in a centered box.

    The visual appearance of `box` and `rbox` is set by a `type` parameter,
    which comes in a dozen or so flavors to call for attention in an
    appropriate manner when displayed. Use the `AboutWikiBoxes` macro for a
    demonstration.

    The width of right aligned boxes is adjustable and configured in the
    `[wikiextras]` section in `trac.ini`.

    The visual appearance of content tables presented to the right, generated
    by the built in `PageOutline` macro, is adjusted to be in line with these
    boxes. The width of the content boxes can be set to coincide with the other
    boxes, or be as narrow as possible. This is configured in the
    `[wikiextras]` section in `trac.ini`.

    **The Icons component must be activated** since warning boxes and the like
    uses the icon library.
    """

    implements(IRequestFilter, ITemplateProvider, IWikiMacroProvider)

    rbox_width = IntOption('wikiextras', 'rbox_width', 300,
                           "Width of right aligned boxes.")

    wide_toc = BoolOption('wikiextras', 'wide_toc', 'false',
                            """Right aligned boxes with table of contents,
                            produced by the `PageOutline` macro, are either
                            as wide as ordinary right aligned boxes (`true`) or
                            narrow (`false`).""")

    shadowless = BoolOption('wikiextras', 'shadowless_boxes', 'false',
                            "Use shadowless boxes.")

    urgency_label = [(WARN, "warn"), (HIGHLIGHT, "highlight"),
                     (ELABORATE, "elaborate"), (NEWS, "news"),
                     (NORMAL, "normal")]

    urgency_bg = {WARN: 'red', HIGHLIGHT: 'yellow', ELABORATE: 'blue',
                  NEWS: 'green', NORMAL: 'white'}

    # map <type> -> (<urgency>, <icon name>, [<synonym>]
    types = {'comment': (ELABORATE, 'comment', []),
             'configure': (NORMAL, 'configure', ['configuration', 'tool']),
             'details': (NORMAL, 'details', ['look', 'magnifier']),
             'discussion': (ELABORATE, 'discussion', ['chat', 'talk']),
             'information': (HIGHLIGHT, 'information', ['note']),
             'news': (NEWS, None, []),
             'nok': (ELABORATE, 'nok', ['bad', 'no']),
             'ok': (ELABORATE, 'ok', ['good', 'yes']),
             'question': (HIGHLIGHT, 'question', ['help']),
             'stop': (WARN, 'stop', ['critical']),
             'tips': (HIGHLIGHT, 'tips', []),
             'warning': (WARN, 'warning', ['bug', 'error', 'important']),
             }

    def __init__(self):
        self.word2type = {}
        for name, data in self.types.iteritems():
            self.word2type[name] = name
            for synonym in data[2]:
                self.word2type[synonym] = name

        # Create width-dependable css files.
        #     (The width option in trac.ini defines outer width, style widths
        #     assigned below are therefore compensated for padding so that
        #     actual width of a box is according to trac.ini.)
        # 1: width for style .wikiextras.box (compensated for padding)
        css_file = resource_filename(__name__, os.path.join(
                'htdocs', 'css', 'boxes-%d.css' % self.rbox_width))
        if not os.path.isfile(css_file):
            fd = open(css_file, 'w')
            #noinspection PyStringFormat
            fd.write('.wikiextras.box.right { width: %dpx; }\n'
                     '.wikiextras.box.icon.center, '
                     '.wikiextras.box.icon.right { width: %dpx; }' %
                     (self.rbox_width - 22, self.rbox_width - 57))
            fd.close()
        # 2: width for style .wiki-toc (compensated for padding)
        css_file = resource_filename(__name__, os.path.join(
                'htdocs', 'css', 'boxes-%d-toc.css' % self.rbox_width))
        if not os.path.isfile(css_file):
            fd = open(css_file, 'w')
            fd.write('.wiki-toc { width: %dpx !important; }' %
                     (self.rbox_width - 22))
            fd.close()

    # IRequestFilter methods

    #noinspection PyUnusedLocal
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        add_stylesheet(req, 'wikiextras/css/boxes.css')
        add_stylesheet(req, 'wikiextras/css/boxes-%d.css' % self.rbox_width)
        if self.wide_toc:
            add_stylesheet(req, 'wikiextras/css/boxes-%d-toc.css' %
                                self.rbox_width)
        else:
            add_stylesheet(req, 'wikiextras/css/boxes-narrow-toc.css')
        if self.shadowless:
            add_stylesheet(req, 'wikiextras/css/boxes-shadowless.css')
        return template, data, content_type

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return [('wikiextras', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

    # IWikiMacroProvider methods

    def get_macros(self):
        yield 'box'
        yield 'rbox'
        yield 'newsbox'
        yield 'imagebox'

    def _get_type_description(self, line_prefix=''):
        urgency = {} # {'urgency': ('color', ["type -words"])}
        # color
        for u, color in self.urgency_bg.iteritems():
            urgency[u] = (color, [])
        # words
        for type, data in self.types.iteritems():
            urg, icon, words = data
            urgency[urg][1].append(type)
            for w in words:
                urgency[urg][1].append(w)
        descr = ["%s||= Urgency ''(box color)'' =||= type =||" % line_prefix]
        for urg, label in self.urgency_label:
            data = urgency[urg]
            color = data[0]
            words = data[1]
            words.sort()
            descr.append("%s||= %s ''(%s)'' =|| %s ||" %
                         (line_prefix, label, color,
                          ', '.join('`%s`' % w for w in words)))
        return '\n'.join(descr)

    #noinspection PyUnusedLocal
    def get_macro_description(self, name):
        if name == 'box':
            return cleandoc("""\
                View wiki text in a box.

                Syntax:
                {{{
                {{{#!box type align=... width=...
                wiki text
                }}}
                }}}
                or preferably when content is short:
                {{{
                [[box(wiki text, type=..., align=..., width=...)]]
                }}}
                where
                 * `type` is an optional flag, or parameter, to call for
                   attention depending on type of matter. When `type` is set,
                   the box is decorated with an icon (except for `news`) and
                   colored, depending on what ''urgency'' the type represents:
                %s
                     `type` may be abbreviated as long as the abbreviation is
                     unique for one of the keywords above.
                 * `align` is optionally one of `right`, `left` or `center`.
                   The `rbox` macro is an alias for `align=right`.
                 * `width` is optional and sets the width of the box (defaults
                   `auto` except for right aligned boxes which defaults a fixed
                   width). `width` should be set when `align=center` for
                   proper results.

                Examples:
                {{{
                {{{#!box warn
                = Warning
                Beware of the bugs
                }}}

                [[box(Beware of the bugs, type=warn)]]
                }}}

                A `style` parameter is also accepted, to allow for custom
                styling of the box. See also the `rbox`, `newsbox` and
                `imagebox` macros (processors).
                """) % self._get_type_description(' ' * 5)
        elif name == 'rbox':
            return cleandoc("""\

                View a right-aligned box. (This is a shorthand for
                `box align=right`)

                Syntax:
                {{{
                {{{#!rbox type width=...
                wiki text
                }}}
                }}}
                or preferably when content is short:
                {{{
                [[rbox(wiki text, type=..., width=...)]]
                }}}
                where
                 * `type` is an optional flag, or parameter, to call for
                   attention depending on type of matter. When `type` is set,
                   the box is decorated with an icon (except for `news`) and
                   colored, depending on what ''urgency'' the type represents:
                %s
                     `type` may be abbreviated as long as the abbreviation is
                     unique for one of the keywords above.
                 * `width` is optional and sets the width of the box (defaults
                   a fixed width). Use `width=auto` for an automatically sized
                   box.

                Examples:
                {{{
                {{{#!rbox warn
                = Warning
                Beware of the bugs
                }}}

                [[rbox(Beware of the bugs, type=warn)]]
                }}}

                A `style` parameter is also accepted, to allow for custom
                styling of the box. See also the `box`, `newsbox` and
                `imagebox` macros (processors).
                """) % self._get_type_description(' ' * 5)
        elif name == 'newsbox':
            return cleandoc("""\
                Present a news box to the right. (This is a shorthand for
                `rbox news`)

                Syntax:
                {{{
                {{{#!newsbox
                wiki text
                }}}
                }}}

                The following parameters are also accepted:
                 * `width` -- Set the width of the box (defaults a fixed
                   width).
                 * `style` -- Custom styling of the box.

                See also the `box`, `rbox` and `imagebox` macros (processors).
                ''(Comment: This box corresponds to the well-known
                ''`NewsFlash`'' macro.)''
                """)
        elif name == 'imagebox':
            return cleandoc("""\
                Present a centered box suitable for one image.

                Syntax:
                {{{
                {{{#!imagebox
                wiki text
                }}}
                }}}

                This box is typically used together with the `Image` macro:
                {{{
                {{{#!imagebox
                [[Image(file)]]

                Caption
                }}}
                }}}

                Note that the `size` parameter of the `Image` macro may not
                behave as expected when using relative sizes (`%`).

                The following parameters are also accepted:
                 * `align` -- One of `right`, `left` or `center` (defaults
                   `center`).
                 * `width` -- Set the width of the box (defaults `auto` except
                   for right aligned boxes which defaults a fixed width).
                 * `style` -- Custom styling of the box.

                See also the `box`, `rbox` and `newsbox` macros (processors).
                """)

    def _get_type(self, word):
        # Accept unique abbrevs. of type
        if not word:
            return ''
        if word in self.word2type:
            return self.word2type[word]
        type = ''
        for w in self.word2type.iterkeys():
            if w.startswith(word):
                t = self.word2type[w]
                if type and type != t:
                    return # 2nd found, not unique
                type = t
        return type

    def _has_icon(self, type):
        if type in self.types:
            return self.types[type][1] is not None

    #noinspection PyUnusedLocal
    def expand_macro(self, formatter, name, content, args=None):
        class_list = ['wikiextras', 'box']
        style_list = []
        if args is None:
            content, args = parse_args(content)

        #noinspection PyArgumentList
        if not Icons(self.env).shadowless:
            class_list.append('shadow')

        class_arg = args.get('class', '')
        if class_arg:
            class_list.append(class_arg)

        align = 'right' if name in ['newsbox', 'rbox'] else \
                'center' if name=='imagebox' else ''
        align = args.get('align', align)
        if align:
            class_list.append(align)

        if name == 'newsbox':
            type = 'news'
        elif name == 'imagebox':
            type = 'image'
        else:
            type = args.get('type')
            if not type:
                for flag, value in args.iteritems():
                    if value is True:
                        type = flag
                        break
            type = self._get_type(type)
        if type in self.types:
            td = self.types[type] # type data
            if td[1]: #icon
                class_list += ['icon', td[1]]
            else:
                class_list.append(type)
            bg = self.urgency_bg.get(td[0])
            if bg:
                class_list.append(bg)
            del td
        elif type:
            class_list.append(type)

        style = args.get('style', '')
        if style:
            style_list.append(style)

        width = args.get('width', '')
        if width:
            if width.isdigit():
                width = '%spx' % width
            if width.endswith('px'):
                # compensate for padding
                if self._has_icon(type):
                    width = '%dpx' % (int(width[:-2]) - 57)
                else:
                    width = '%dpx' % (int(width[:-2]) - 22)
            style_list.append('width:%s' % width)

        html = format_to_html(self.env, formatter.context, content)
        class_ = ' '.join(class_list)
        style = ';'.join(style_list)

        return tag.div(html, class_=class_, style=style)


class AboutWikiBoxes(Component):
    """Macro for displaying a wiki page on how to use boxes.

    Create a wiki page `WikiBoxes` and insert the following line to show
    detailed instructions to wiki authors on how to use boxes in wiki pages:
    {{{
    [[AboutWikiBoxes]]
    }}}
    """

    implements(IWikiMacroProvider)

    # IWikiMacroProvider methods

    def get_macros(self):
        yield 'AboutWikiBoxes'

    #noinspection PyUnusedLocal
    def get_macro_description(self, name):
        return "Display a wiki page on how to use boxes."

    #noinspection PyUnusedLocal
    def expand_macro(self, formatter, name, content, args=None):
        help_file = resource_filename(__name__, 'doc/WikiBoxes')
        fd = open(help_file, 'r')
        wiki_text = fd.read()
        fd.close()
        return format_to_html(self.env, formatter.context, wiki_text)
