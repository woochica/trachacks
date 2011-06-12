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

"""Decorate wiki text with colors.
"""

from inspect import cleandoc

from genshi.builder import tag
from genshi.core import Markup

from trac.core import implements, Component
from trac.wiki import IWikiMacroProvider, format_to_html, format_to_oneliner


class Color(Component):
    """Macro for coloring wiki text.

    Use the `Color` macro to decorate text with colors.
    """

    implements(IWikiMacroProvider)

    # IWikiMacroProvider methods

    def get_macros(self):
        yield 'Color'

    #noinspection PyUnusedLocal
    def get_macro_description(self, name):
        return cleandoc("""Decorate text with colors.

                Syntax:
                {{{
                [[Color(text, fg/bg/size)]]
                }}}
                where
                 * `text` is the text to decorate. Enter a leading and/or
                   trailing space character to surround the text with a
                   decorated space.
                 * `fg/bg/size` defines the foreground and background colors,
                   and a font size. All parameters are optional and separated
                   by slash character (`/`).

                Colors may be specified as an RGB triplet in hexadecimal format
                (a hex triplet; e.g. `#000` or `#000000` for black); they may
                also be specified according to their common English names (e.g.
                red, green, blue etc.). See
                [http://en.wikipedia.org/wiki/Web_colors here] for details.

                Examples:
                {{{
                [[Color(Large red on yellow, red/yellow/150%)]]
                [[Color(Red on yellow, red/yellow)]]
                [[Color(Yellow background, /yellow)]]
                [[Color(Large red, #f00/2em)]]
                [[Color(Large on yellow, /yellow/20px)]]
                [[Color(Text, can, have, commas, /yellow)]]
                [[Color( Surrounding space is also decorated , white/red)]]
                }}}

                To set the foreground color for a larger block, the processor
                variant can be used ''(background color and font size may not
                display as expected due to the mechanisms of cascading style
                sheets, be advised and use the ''color'' parameter only)'':
                 
                {{{
                {{{#!Color color=green
                ...
                }}}
                }}}
                """)

    #noinspection PyUnusedLocal
    def expand_macro(self, formatter, name, content, args=None):
        style_args = {'fg': 'color', 'bg': 'background-color',
                      'size': 'font-size'}
        style_values = {'color': '', 'background-color': '', 'font-size': ''}
        space_start = ''
        space_end = ''
        if args:
            text = content
            for k in args.keys():
                style = style_args[k] if k in style_args else k
                style_values[style] = args.get(k)
            html = format_to_html(self.env, formatter.context, text)
        else:
            args = content.split(',')
            text = ','.join(args[:-1])
            args = args[-1].split('/') + ['']*3
            style_values['color'] = args.pop(0).strip()
            # background color is optional
            arg = args.pop(0).strip()
            if len(arg) > 0 and arg[0].isdigit():
                style_values['font-size'] = arg
            else:
                style_values['background-color'] = arg
                style_values['font-size'] = args.pop(0).strip()
            html = format_to_oneliner(self.env, formatter.context, text)
            if text.startswith(u' '):
                space_start = Markup('&nbsp')
            if text.endswith(u' '):
                space_end = Markup('&nbsp')
        if style_values['font-size'].isdigit():
            style_values['font-size'] += '%'
        style = ';'.join('%s:%s' % (k, v) for (k, v) in
                         style_values.iteritems() if v)
        return tag.span(space_start, html, space_end, style=style)
