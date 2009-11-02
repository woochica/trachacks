# Copyright (c) 2008 Martin Scharrer <martin@scharrer-online.de>
# This is Free Software under the GPLv3 or BSD license.
#
# $Id$
#

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]

from  trac.core       import  *
from  trac.wiki.api   import  IWikiMacroProvider
from  genshi.builder  import  tag

from  parseargs       import  parse_args

class ParseArgsTestMacro(Component):
    """Test macro for `tracadvparseargs.parse_args` function.

This macro is intended to be used by the developers of the above function to 
simplify the testing process and has no real value for normal Trac users.

== Macro usage ==
{{{
[[ParseArgsTest(parser_options|||arguments_to_parse)]]
}}}
will call
{{{
#!python
parse_args(arguments_to_parse, **parser_options)
}}}
and will display its return value. See below for the list of parser options.

== Example ==
{{{
[[ParseArgsTest(strict=True,delquotes=True|||key1=val1,key2="val2a,val2b")]]
}}}
will call
{{{
parse_args('key1=val1,key2="val2a,val2b"', strict=True, delquotes=True)
}}}
    """
    implements ( IWikiMacroProvider )

    ### methods for IWikiMacroProvider
    def expand_macro(self, formatter, name, content):
        args, rcontent = content.split('|||',2)
        try:
            ldummy, pa = parse_args (args)
            largs, kwargs = parse_args (rcontent, **pa)
        except EndQuoteError, e:
            raise TracError( str(e) )
        return tag.div(
              tag.p("largs  = ", largs.__repr__()),
              tag.p("kwargs = ", kwargs.__repr__()),
              class_='advparseargs'
            )

    def get_macros(self):
        yield 'ParseArgsTest'

    def get_macro_description(self, name):
        return self.__doc__ + parse_args.__doc__

