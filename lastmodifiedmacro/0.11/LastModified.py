# Author: Steven N. Severinghaus <sns@severinghaus.org>
# Last Modified: 2008-09-23 by Bill Coffman <bill.coffman@gmail.com>
# Home: http://trac-hacks.org/wiki/LastModifiedMacro
#
# The LastModified macro is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation; either version 2 of the License, or (at
# your option) any later version.
#
# Created for the BFGFF project, http://chimp.acm.uiuc.edu/
#
# Shows the last modification date of the specified page, or the page the
# macro appears in if not specified. An optional argument,  delta, can be
# given to show the time elapsed since the last modification. The output is
# placed in span with a title that gives the exact modification date and
# the author of the change.
#
# For example, [[LastModified(CustomMacros)]] produces:
#   09/06 20:34
#
# Alternatively, [[LastModified(CustomMacros,delta)]] produces:
#   5 weeks
#

from StringIO import StringIO
from datetime import datetime

from trac.resource import get_resource_name
from trac.util.datefmt import format_datetime, utc
from trac.util.html import Markup
from trac.wiki.formatter import Formatter
from trac.wiki.macros import WikiMacroBase, parse_args

revision = "$Rev$"
url = "$URL$"

class LastModifiedMacro(WikiMacroBase):

    """Displays the last modified time of the specified wiki page."""
    revision = "$Rev$"
    url = "$URL$"

    def expand_macro(self, formatter, name, content):

        args, _ = parse_args(content)
        
        if not args:
            page_name = get_resource_name( self.env, formatter.resource )
            mode='normal'
        elif len(args) == 1:
            page_name=args[0]
            mode='normal'
        else:
            page_name=args[0]
            mode='delta'

        db=self.env.get_db_cnx()
        cursor=db.cursor()
        cursor.execute("SELECT author, time FROM wiki WHERE name = '%s' "
                       "ORDER BY version DESC LIMIT 1" % page_name)
        row = cursor.fetchone()
        if not row:
            out = StringIO('cannot find "' + page_name + '"')
            return Markup(out.getvalue())

        username   = row[0]
        time_int = row[1]
        
        # see if there's a fullname associated with username
        cursor.execute("SELECT value FROM session_attribute "
                       "WHERE sid = '%s' AND name = 'name'" % username)
        row = cursor.fetchone()
        if not row:
            author = username
        else:
            author = row[0]        

        last_mod = datetime.fromtimestamp(time_int, utc)
        now      = datetime.now(utc)
        elapsed  = now - last_mod
        if mode=='delta':
            if elapsed.days==0:
                if elapsed.seconds/3600>1.5:
                    count=elapsed.seconds/3600
                    unit='hour'
                elif elapsed.seconds/60>1.5:
                    count=elapsed.seconds/60
                    unit='minute'
                else:
                    count=elapsed.seconds
                    unit='second'
            elif elapsed.days/3650>1.5:
                count=elapsed.days/3650
                unit='decade'
            elif elapsed.days/365>1.5:
                count=elapsed.days/365
                unit='year'
            elif elapsed.days/30>1.5:
                count=elapsed.days/30
                unit='month'
            elif elapsed.days/7>1.5:
                count=elapsed.days/7
                unit='week'
            else:
                count=elapsed.days
                unit='day'
            text =""+repr(count)+" "+unit
            if (count != 1 and count != -1): text+="s"
        else:
            text = format_datetime(last_mod, '%c')
            text = format_datetime(last_mod, '%m/%d %k:%M')

        out = StringIO(text)
        return Markup(out.getvalue())

