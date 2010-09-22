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

from  trac.core          import  *
from  genshi.builder     import  tag, Markup
from  trac.util.datefmt  import  datetime, utc


# Try to use babels format_datetime to localise date-times if possible.
# A fall back to tracs implementation strips the unsupported `locale` argument.
from  trac.util.datefmt      import  format_datetime as trac_format_datetime
try:
    from  babel.dates        import  format_datetime, LC_TIME
except ImportError:
    LC_TIME = None
    def format_datetime(t=None, format='%x %X', tzinfo=None, locale=None):
        return trac_format_datetime(t, format, tzinfo)

try:
    from  babel.dates        import  get_datetime_format, get_date_format, get_time_format, DateTimePattern
    def datetime_format(format='medium', locale=LC_TIME):
        time_format = unicode(get_time_format(format, locale))\
                .replace('HH','%H')\
                .replace('h','%l')\
                .replace('a','%p')\
                .replace('mm','%i')\
                .replace('ss','%S')
        date_format = unicode(get_date_format(format, locale))\
                .replace('yyyy','%Y')\
                .replace('MMM','%b')\
                .replace('MM','%m')\
                .replace('dd','%X')\
                .replace('d','%e')\
                .replace('%X','%d')
        return get_datetime_format(format, locale)\
                .replace('{0}', time_format)\
                .replace('{1}', date_format)
except ImportError:
    def datetime_format(format='medium', locale=LC_TIME):
        return u"%Y-%m-%d %H:%i:%s"

try:
    from  trac.util.datefmt  import  to_utimestamp
    def current_timestamp():
        return to_utimestamp( datetime.now(utc) )
except ImportError:
    def current_timestamp():
        return to_timestamp( datetime.now(utc) )


def moreless(text, length):
    """Turns `text` into HTML code where everything behind `length` can be uncovered using a ''show more'' link
       and later covered again with a ''show less'' link."""
    try:
        if len(text) <= length:
            return tag(text)
    except:
        return tag(text)
    return tag(tag.span(text[:length]),tag.a(' [', tag.strong(Markup('&hellip;')), ']', class_="more"),
        tag.span(text[length:],class_="moretext"),tag.a(' [', tag.strong('-'), ']', class_="less"))


def ensure_iter( var ):
    """Ensures that variable is iterable. If it's not by itself, return it
       as an element of a tuple"""
    if getattr(var, '__iter__', False):
        return var
    return (var,)


def ensure_tuple( var ):
    """Ensures that variable is a tuple, even if its a scalar"""
    if getattr(var, '__iter__', False):
        return tuple(var)
    return (var,)


def ensure_string( var ):
    """Ensures that variable is a string"""
    if getattr(var, '__iter__', False):
        return unicode(u','.join(var))
    else:
        return var


def decode_range( str ):
    """Decodes given string with integer ranges like `a-b,c-d` and yields a list
       of tuples: [(a,b),(c,d)] in this ranges."""
    for irange in unicode(str).split(','):
        irange = irange.strip()
        try:
            index = irange.index('-')
        except:
            if irange == '*':
                a, b = 0, None
            else:
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


def convert_to_sql_wildcards( pattern ):
    r"""Converts wildcards '*' and '?' to SQL versions '%' and '_'.
       A state machine is used to allow for using the backslash to
       escape this characters:
           test -> test
           test* -> test%
           test\* -> test*
           test\\* -> test\%
           test\\\* -> test\*
           test\\\\* -> test\\%
           test\\\\\* -> test\\*
    """
    pat = ''
    esc = False
    for p in pattern:
        if not p in '*?\\':
            if esc:
                pat += '\\'
                esc = False
            pat += p
        else:
            if esc:
                esc = False
                pat += p
            else:
                if p == '\\':
                    esc = True
                elif p == '*':
                    pat += '%'
                elif p == '?':
                    pat += '_'
    return pat

# EOF
