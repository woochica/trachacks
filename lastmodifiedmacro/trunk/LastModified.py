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

from trac.core import TracError
from trac.resource import get_resource_name
from trac.util.datefmt import format_datetime, to_datetime
from trac.util.html import Markup
from trac.wiki.macros import WikiMacroBase, parse_args

revision = "$Rev$"
url = "http://trac-hacks.org/wiki/LastModifiedMacro"
author = "Steven N. Severinghaus"
author_email = "<sns@severinghaus.org>"

class LastModifiedMacro(WikiMacroBase):
    """Displays the last modified date a wiki page.
    
    If no arguments are provided, the last modified date of the page
    containing the macro is displayed. A wiki page name can be specified
    as the first argument. An optional argument, delta, can be given to
    show the time elapsed since the last modification.

    Examples:
     * `[[LastModified(WikiMacros)]]` produces: [[LastModified(WikiMacros)]]
     * `[[LastModified(WikiMacros,delta)]]` produces: [[LastModified(WikiMacros,delta)]]
    """

    def expand_macro(self, formatter, name, content):

        args, kwargs = parse_args(content)
        
        if not args:
            page_name = get_resource_name(self.env, formatter.resource)
            mode = 'normal'
        elif len(args) == 1:
            page_name = args[0]
            mode = 'normal'
        else:
            page_name = args[0]
            mode = 'delta'

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT author, time FROM wiki WHERE name = '%s' "
                       "ORDER BY version DESC LIMIT 1" % page_name)
        row = cursor.fetchone()
        if not row:
            raise TracError('Wiki page "%s" not found.' % page_name)

        username = row[0]
        time_int = row[1]
        
        # see if there's a fullname associated with username
        cursor.execute("SELECT value FROM session_attribute "
                       "WHERE sid = '%s' AND name = 'name'" % username)
        row = cursor.fetchone()
        if not row:
            author = username
        else:
            author = row[0]

        if mode == 'delta':
            last_mod = to_datetime(time_int)
            now = to_datetime(None)
            elapsed = now - last_mod
            if elapsed.days == 0:
                if elapsed.seconds / 3600 > 1.5:
                    count = elapsed.seconds / 3600
                    unit = 'hour'
                elif elapsed.seconds / 60 > 1.5:
                    count = elapsed.seconds / 60
                    unit = 'minute'
                else:
                    count = elapsed.seconds
                    unit = 'second'
            elif elapsed.days / 3650 > 1.5:
                count = elapsed.days / 3650
                unit = 'decade'
            elif elapsed.days / 365 > 1.5:
                count = elapsed.days / 365
                unit = 'year'
            elif elapsed.days / 30 > 1.5:
                count = elapsed.days / 30
                unit = 'month'
            elif elapsed.days / 7 > 1.5:
                count = elapsed.days / 7
                unit = 'week'
            else:
                count = elapsed.days
                unit = 'day'
            text = "" + repr(count) + " " + unit
            if (count != 1 and count != -1): text += "s"
        else:
            text = format_datetime(time_int, '%c')

        return Markup(text)

