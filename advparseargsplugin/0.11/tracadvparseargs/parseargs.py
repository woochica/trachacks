# Copyright (c) 2008 Martin Scharrer <martin@scharrer-online.de>
# This is Free Software under the GPLv3 or BSD license.
#
# $Id$
#
from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from trac.wiki.macros import WikiMacroBase
__all__ = ['parse_args','EndQuoteError']

__url__      = r"$URL$"[6:-2]
__author__   = r"$Author$"[9:-2]
__revision__ = int(r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]


def parse_args (args, strict = True, multi = False, listonly = False, minlen = 0,
        quotechar = '"', escchar = '\\', delim = ',', delquotes = False):
    """Parses a comma separated string were the values can include multiple quotes.

       Website: http://trac-hacks.org/wiki/AdvParseArgsPlugin

       $Id$

       Parameters:
        args:: The argument string; 'content' in `expand_macro.
        strict:: Enables strict checking of keys.
        multi:: Enables folding of muliple given keys into list.
                If set to `True` values of multiple given keys will be returned
                as list, but single given keys will return a scalar.
                If set to a list only the values of the listed keys will be
                returned as list, but always as list even when there is only one
                value.
                If this list contains `'*'`, __all__ values are __always__ 
                returned as list.
        listonly:: If true only a list is returned, no directionary.
        minlen:: Extend returned list to given minimum length. Only used when
                 `listonly=True`.
       Parser parameters:
        quotechar:: The quote character to be used.
        escchar:: The escape character to be used.
        delim:: The delimiter character to be used.
        delquotes:: Selects if quotes should be removed.
    """
    largs  = []
    kwargs = {}

    # Handle multi list:
    multiset = set()
    alwayslist = False
    if multi and isinstance(multi, list):
        multiset = set(multi)
        multi = True
        alwayslist = '*' in multiset

    def strip (arg):
        """Strips surrounding quotes, but only if the arg doesn't includes any
        other quotes."""
        arg.strip()
        if arg.startswith( quotechar ) and arg.endswith( quotechar ) \
          and  ( len(arg) == 2 or arg[1:-1].find( quotechar ) == -1 ):
            return arg[1:-1]
        else:
            return arg

    def checkkey (arg):
        import re
        if listonly:
            largs.append( strip( arg ) )
            return
        if strict:
            m = re.match(r'\s*[a-zA-Z_]\w*=', arg)
        else:
            m = re.match(r'\s*[^=]+=', arg)
        if m:
            kw = arg[:m.end()-1].strip()
            value = strip( arg[m.end():] )
            if strict:
                kw = unicode(kw).encode('utf-8')

            if not multi:
                kwargs[kw] = value
            elif not multiset:
                if kw in kwargs:
                    if isinstance(kwargs[kw], list):
                        kwargs[kw].append( value )
                    else:
                        kwargs[kw] = [ kwargs[kw], value ]
                else:
                    kwargs[kw] = value
            elif alwayslist or kw in multiset:
                if kw not in kwargs:
                    kwargs[kw] = []
                kwargs[kw].append(value)
            else:
                kwargs[kw] = value
        else:
            largs.append( strip( arg ) )

    if args:
        # Small parser to split on commas
        #  * Ignores commas in double quotes
        #  * Backslash escapes any following character
        esc   = False   # last char was escape char
        quote = False   # inside quote
        arg = ''
        for char in args:
            if esc:
                esc = False
                arg += char
            elif char == quotechar:
                quote = not quote
                if not delquotes:
                    arg += char
            elif char == escchar:
                esc = True
            elif char == delim and not quote:
                checkkey( arg )
                arg = ''
            else:
                arg += char
        if quote:
            raise EndQuoteError
        checkkey( arg )

    if listonly:
        # extend to minimum length:
        d = minlen - len(largs)
        if d > 0:
            largs.extend([''] * d)
        return largs
    else:
        return largs, kwargs


class EndQuoteError(Exception):
    """Exception raised if argument string ends while quotation is still open."""
    message = "Found end of argument string while looking for closing quote!"

    def __init__ (self, message=''):
        if message:
            self.message = message

    def __str__ (self):
        return self.message

