# -*- coding: utf-8 -*-
"""
This macro allows you to add color.

Author: David Roussel
Author: andyhan
"""

from genshi.builder import tag
from trac.wiki.formatter import format_to_oneliner
from trac.wiki.macros import WikiMacroBase

revision="$Rev$"
url="http://trac-hacks.org/wiki/ColorMacro"

class ColorMacro(WikiMacroBase):
    """Usage:
    {{{
      [[Color(background-color, color, text)]]
    }}}
    or
    {{{
      [[Color(color, text)]]
    }}}
    Where: 
    color::
      is a color keyword or hex color number recognized by your browser
    text::
      any wiki markup you like
    
    Example:
    {{{
      [[Color(red,This has a red background)]]
      [[Color(blue, green,This has a blue background and green text)]]
    }}}
    """
    def expand_macro(self, formatter, name, args):
        args = tuple(args.split(','))
        if len(args) == 2 :
          return tag.span(format_to_oneliner(self.env, formatter.context, args[1]),
                          style='background-color: %s' % args[0])
        else:
          return tag.span(format_to_oneliner(self.env, formatter.context, args[2]),
                          style='background-color: %s; color: %s' % args[0:2])
