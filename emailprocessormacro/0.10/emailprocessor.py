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
from trac.wiki.api import IWikiMacroProvider
from trac.util.text import wrap
from trac.util.html import Markup

class EmailMacro(WikiMacroBase):
    """Email wrapping formatter

    This macro takes an email message and will wrap lines to 72 characters.
    It will also put the emails inside a preformatted block.

    Invocation:
    {{{
    #!email
    <email stuff here>
    }}}

    """

    def get_macros(self):
        """Yield the name of the macro based on the class name."""
        yield 'email'
        yield 'Email'

    def render_macro(self, req, name, content): 
        text = wrap(content, cols=72)
        return Markup("<pre class='wiki'>%s</pre>" % text)
    
