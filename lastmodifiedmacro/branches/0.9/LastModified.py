# Author: Steven N. Severinghaus <sns@severinghaus.org>
# Last Modified: 2006-04-14
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
#   <span class="last-modified" title="Wed Oct  6 20:34:51 2004 by sevrnghs">2004-10-06</span>
#
# Alternatively, [[LastModified(CustomMacros,delta)]] produces:
#   <span class="last-modified" title="Wed Oct  6 20:34:51 2004 by sevrnghs">7 weeks</span>
#
# This is a CSS style to apply that will make it about 3.14% slicker:
#   span.last-modified { border-bottom: 1px dotted gray; cursor: help; }
#

import time
import datetime
import re

def execute(hdf, txt, env):
    if not txt:
        page_name=hdf.getValue('title', '')
        page_name=re.sub(' \(.*$', '', page_name)
        page_name=page_name or 'WikiStart'
        mode='normal'
    elif txt.find(',')==-1:
        if txt=='delta':
            mode='delta'
            page_name=hdf.getValue('title', '')
            page_name=re.sub(' \(.*$', '', page_name)
            page_name=page_name or 'WikiStart'
        else:
            page_name=txt
            mode='normal'
    else:
        args=txt.split(',',1)
        page_name=args[0]
        mode=args[1]

    db=env.get_db_cnx()
    cursor=db.cursor()
    cursor.execute("SELECT author, time FROM wiki WHERE name = '%s' "
            "ORDER BY version DESC LIMIT 1" % page_name)
    row=cursor.fetchone()
    author=row[0]
    time_int=row[1]
    timestamp=time.localtime(time_int)

    if mode=='delta':
        now=datetime.datetime.utcfromtimestamp(time.time())
        last_modified=datetime.datetime.utcfromtimestamp(time_int)
        elapsed=now-last_modified
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
        output=""+repr(count)+" "+unit
        if (count != 1 and count != -1): output+="s"
    else:
        output=time.strftime("%Y-%m-%d", timestamp)

    wrapped_output='<span class="last-modified" title="'+\
            time.asctime(timestamp)+' by '+author+'">'+\
            output+'</span>'

    return wrapped_output

