# -*- coding: utf-8 -*-
"""
This macro allows you to add color.

Author: David Roussel
Author: andyhan
"""

from trac.wiki.macros import WikiMacroBase

revision="$Rev$"
url="http://trac-hacks.org/wiki/ColorMacro"

class ColorMacro(WikiMacroBase):
    """Usage:
    {{{
      [[Color( background-color, color , text )]]
    }}}
    or
    {{{
      [[Color( color , text )]]
    }}}
    Where: 
    color::
      is a color keyword or hex color number recognised by your browser
    text::
      any text or html you like
    
    Example:
    {{{
      [[Color(red,This has a red background)]]
      [[Color(blue, green,This has a blue background and green text)]]
    }}}
    """
    def expand_macro(self, formatter, name, args):
        args = tuple(args.split(","))
        if len(args) == 2 :
          return '<span style="background-color:%s;padding: 0.1ex 0.4em;">%s</span>' % args
        else:
          return '<span style="background-color:%s;padding: 0.1ex 0.4em;color:%s;">%s</span>' % (args[0], args[1], ','.join(args[2:]))
