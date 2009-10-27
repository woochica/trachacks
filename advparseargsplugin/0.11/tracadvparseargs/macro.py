# Copyright (c) 2008 Martin Scharrer <martin@scharrer-online.de>
# This is Free Software under the GPLv3 or BSD license.
#
# $Id$
#

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int(r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]

from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from parseargs import parse_args

class ParseArgsTestMacro(Component):
    implements(IWikiMacroProvider)

    ### methods for IWikiMacroProvider
    def expand_macro(self, formatter, name, content):
        """Test macro for parse_args."""
        args, rcontent = content.split('|||',2)
        try:
            ldummy, pa = parse_args (args)
            largs, kwargs = parse_args (rcontent, **pa)
        except EndQuoteError, e:
            raise TracError( str(e) )
        return unicode((largs, kwargs))

    def get_macros(self):
        return ('ParseArgsTest',)

    def get_macro_description(self, name):
      return """Test macro for `tracadvparseargs.parse_args` function.
        """ + parse_args.__doc__

