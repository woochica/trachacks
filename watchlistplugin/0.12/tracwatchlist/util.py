# -*- coding: utf-8 -*-
"""
= Watchlist Plugin for Trac =
Plugin Website:  http://trac-hacks.org/wiki/WatchlistPlugin
Trac website:    http://trac.edgewall.org/

Copyright (c) 2008-2010 by Martin Scharrer <martin@scharrer-online.de>
All rights reserved.

The i18n support was added by Steffen Hoffmann <hoff.st@web.de>.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For a copy of the GNU General Public License see
<http://www.gnu.org/licenses/>.

$Id$
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


def ldml_patterns( ldml_pattern ):
    """Takes a LDML date/time format pattern and breaks it down into its
       elements"""
    last = None
    num = 1
    patterns = []
    verbatim = False
    verbtext = ''
    for s in ldml_pattern:
        if verbatim:
            if last == "'":
                if s == "'":
                    # Inside quote (quote character already added)
                    last = None
                    continue
                else:
                    # Last character ended verbatim
                    if verbtext != "'":
                        verbtext = verbtext[:-1]
                    patterns.append( [verbtext] )
                    last = None
                    verbatim = False
            else:
                verbtext += s
                last = s
                continue
        if s == "'":
            verbatim = True
            verbtext = ''
            if not last is None:
                patterns.append( last * num )
            num = 1
            last = None
        elif s == last:
            num+=1
        else:
            if not last is None:
                patterns.append( last * num )
            num = 1
            last = s
    # Flush buffers
    if verbatim:
        if last == "'" and verbtext:
            verbtext = verbtext[:-1]
        patterns.append( [verbtext ] )
    else:
        if not last is None:
            patterns.append( last * num )
    return patterns

_PATTERN_TRANSLATION = {
    'h'     : '%l',
    'hh'    : '%h',
    'H'     : '%k',
    'HH'    : '%H',
    'K'     : '%l', # fuzzy
    'KK'    : '%h', # fuzzy
    'k'     : '%k', # fuzzy
    'kk'    : '%H', # fuzzy
    'j'     : '?',
    'jj'    : '?',
    'a'     : '%p',
    'm'     : '%i', # fuzzy
    'mm'    : '%i',
    's'     : '%S',
    'ss'    : '%S',
    'S'     : '?',
    'A'     : '?',
    'z'     : '%@',
    'zz'    : '%@',
    'zzz'   : '%@',
    'zzzz'  : '%@', # fuzzy
    'Z'     : '%+',
    'ZZ'    : '%+',
    'ZZZ'   : '%+',
    'ZZZZ'  : 'GMT%+',
    'v'     : '%@', # fuzzy
    'vvvv'  : '%@', # fuzzy
    'V'     : '%@', # fuzzy
    'VVVV'  : '%@', # fuzzy
    'Q'     : '?', # quarter
    'q'     : '?', # quarter
    'yyyy'  : '%Y',
    'yy'    : '%y',
    'M'     : '%c',
    'MM'    : '%m',
    'MMM'   : '%b',
    'MMMM'  : '%M',
    'MMMMM' : '?',
    'L'     : '%c',
    'LL'    : '%m',
    'LLL'   : '%b',
    'LLLL'  : '%M',
    'LLLLL' : '?',
    'l'     : '*',
    'w'     : '?', # week of the year
    'ww'    : '??',
    'W'     : '?', # week of the month
    'd'     : '%e',
    'dd'    : '%d',
    'D'     : '?',
    'DD'    : '??',
    'DDD'   : '???',
    'F'     : '%w',
    'g'     : '?',
    'E'     : '%a',
    'EE'    : '%a',
    'EEE'   : '%a',
    'EEEE'  : '%W',
    'EEEEE' : '?',
    'e'     : '%w',
    'ee'    : '%w',
    'eee'   : '%a',
    'eeee'  : '%W',
    'eeeee' : '?',
    'c'     : '%w',
    'cc'    : '%w',
    'ccc'   : '%a',
    'cccc'  : '%W',
    'ccccc' : '?',
    'G'     : '%E', # Era abbreviation*
    'GG'    : '%E', # Era abbreviation*
    'GGG'   : '%E', # Era abbreviation*
    'GGGG'  : '%E', # Era abbreviation*
    'GGGGG' : '%E', # Era abbreviation*
}



def convert_LDML_to_MySQL( ldml_pattern ):
    """Converts from LDML date/time format patterns to the one used by MySQL.
       That is the same format used by the Any+Time datepicker currently used.
       See http://www.ama3.com/anytime/#AnyTime.Converter.format
       and http://unicode.org/reports/tr35/#Date_Format_Patterns .
       """
    import re
    result = ''
    for pattern in ldml_patterns(ldml_pattern):
        if isinstance(pattern,list):
            # Verbatim
            result += ''.join(pattern).replace('%','%%')
        else:
            tp = _PATTERN_TRANSLATION.get(pattern,None)
            if tp is None: # Replace unknown letters with '?'
                tp = re.sub(r'[A-Za-z]','?', pattern)
            result += tp
    return result


try:
    from  babel.dates        import  get_datetime_format, get_date_format, get_time_format
    def datetime_format(format='medium', locale=LC_TIME):
        time_format = unicode(get_time_format(format, locale))
        date_format = unicode(get_date_format(format, locale))
        return convert_LDML_to_MySQL( get_datetime_format(format, locale)\
                .replace('{0}', time_format)\
                .replace('{1}', date_format) )
except ImportError:
    def datetime_format(format='medium', locale=LC_TIME):
        return u"%Y-%m-%d %H:%i:%s"

try:
    from  trac.util.datefmt  import  to_utimestamp
    def current_timestamp():
        return to_utimestamp( datetime.now(utc) )
except ImportError:
    from  trac.util.datefmt  import  to_timestamp
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


def ensure_string( var, sep=u',' ):
    """Ensures that variable is a string"""
    if getattr(var, '__iter__', False):
        return unicode(sep.join(var))
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


def convert_to_sql_wildcards( pattern, sql_escape = '|' ):
    r"""Converts wildcards '*' and '?' to SQL versions '%' and '_'.
       A state machine is used to allow for using the backslash to
       escape this characters:
            t\e\s\t -> test
            test -> test
            test* -> test%
            test\* -> test*
            test\\* -> test\%
            test\\\* -> test\*
            test\\\\* -> test\\%
            test\\\\\* -> test\\*
            % -> \%
            _ -> \_
            test_test% -> test\_test\%
            test__test% -> test\_\_test\%
            test\_test\% -> test\_test\%
            test\\_test\\% -> test\\_test\\%
            test\\\_test\\\% -> test\\_test\\%
            test\\\\_test\\\% -> test\\\_test\\%
    """
    pat = ''
    esc = False
    for p in pattern:
        if not p in '*?\\':
            esc = False
            if p in '%_':
                # Escaped for SQL
                pat += sql_escape
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
