# -*- coding: utf-8 -*-
"""
 Watchlist Plugin for Trac
 Copyright (c) 2008-2010  Martin Scharrer <martin@scharrer-online.de>
 This is Free Software under the BSD license.

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + ur"$Rev$"[6:-2].strip('M'))
__date__     = ur"$Date$"[7:-2]

from  trac.core       import  *
from  genshi.builder  import  tag, Markup


def moreless(text, length):
    """Turns `text` into HTML code where everything behind `length` can be uncovered using a ''show more'' link
       and later covered again with a ''show less'' link."""
    return tag(tag.span(text[:length]),tag.a(' [', tag.strong(Markup('&hellip;')), ']', class_="more"),
        tag.span(text[length:],class_="moretext"),tag.a(' [', tag.strong('-'), ']', class_="less"))


def ensure_tuple( var ):
    """Ensures that variable is a tuple, even if its a scalar"""
    if isinstance(var,tuple):
        return var
    if getattr(var, '__iter__', False):
        return tuple(var)
    return (var,)


def decode_range( str ):
    """Decodes given string with integer ranges like `a-b,c-d` and yields a list
       of tuples: [(a,b),(c,d)] in this ranges."""
    for irange in unicode(str).split(','):
        try:
            index = irange.index('-')
        except:
            a = b = irange
        else:
            b = irange[index+1:]
            a = irange[:index]
        try:
            a = int(a)
        except:
            a = None
        try:
            b = int(b)
        except:
            b = None
        if not (a is None and b is None):
            yield (a,b)


def decode_range_sql( str ):
    """Decodes given string with ranges like `a-b,c-d` and returns a SQL
       command fragment to much this ranges."""
    cmd = []
    for (a,b) in decode_range( str ):
        if a is None:
            if b is None:
                continue
            cmd.append( ' ( %%(var)s <= %i ) ' % (b) )
        elif b is None:
            cmd.append( ' ( %%(var)s >= %i ) ' % (a) )
        else:
            cmd.append( ' ( %%(var)s BETWEEN %i AND %i ) ' % (a,b) )
    return ' OR '.join(cmd)
