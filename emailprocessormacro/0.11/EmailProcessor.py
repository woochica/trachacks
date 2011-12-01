# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 John Hampton <pacopablo@pacopablo.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: John Hampton <pacopablo@pacopablo.com>

from trac.wiki.macros import WikiMacroBase
from trac.util import escape
from trac.util.text import wrap

revision="$Rev$"
url="http://trac-hacks.org/wiki/EmailProcessorMacro"

__all__ = ['EmailMacro']

class EmailMacro(WikiMacroBase):
    """Email wrapping formatter

    This macro takes an email message and will wrap lines to 
    72 characters (default), or a length specified.  It will
    also put the emails inside a preformatted block.

    Invocation:
    {{{
    #!email
    <email stuff here>
    }}}
    To wrap to a specified length, the line imediately following
    the invocation should contain `cols: ` followed by the number
    of columns at wich we wrap.  For example:
    {{{
    #!email
    cols: 40
    <email stuff here>
    }}}
    It is important that the `cols:` starts at the beginning of
    the line and that only a number follows it.

    """

    def get_macros(self):
        """Yield the name of the macro based on the class name."""
        yield 'email'
        yield 'Email'

    def expand_macro(self, formatter, name, args):
        text = ''
        if args:
            lines = args.split('\n')
            if lines[0].startswith('cols:'):
                try:
                    width = int(lines[0][5:].strip())
                    lines.pop(0)
                except ValueError:
                    width = 72
            else:
                width = 72
            text = wrap('\n'.join(lines), cols=width)
        return '<pre class="wiki">%s</pre>' % escape(text)
    
