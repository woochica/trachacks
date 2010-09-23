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

from  pkg_resources          import  resource_filename
from  datetime               import  datetime
import os

from  trac.core              import  *
from  genshi.builder         import  tag
from  trac.web.api           import  IRequestHandler, HTTPNotFound
from  trac.wiki.formatter    import  format_to_html
from  trac.mimeview.api      import  Context
from  trac.util.text         import  unicode_unquote, to_unicode
from  tracwatchlist.util     import  LC_TIME


class WatchlistManual(Component):
    implements( IRequestHandler )

    manuals = {}

    def __init__(self):
        dir = resource_filename('tracwatchlist', 'manuals')
        for page in os.listdir(dir):
            if page == '.svn':
                continue
            language = page.strip('.txt').replace('_','-')
            filename = os.path.join(dir, page)
            if os.path.isfile(filename):
                self.manuals[language] = filename


    ## Methods for IRequestHandler ##########################################
    def match_request(self, req):
        return req.path_info.startswith("/watchlist/manual")


    def process_request(self, req):
        path = req.path_info[ len("/watchlist/manual") : ].strip('/')
        if path.startswith('attachments'):
            return self.handle_attachment(req, path)

        language = path
        if not language:
            language = req.session.get('language', 'en-US')

        # Try to find a suitable language if no manual exists
        # in the requested one.
        if language not in self.manuals:
            # Try to find a main language,
            # e.g. 'xy' instead of 'xy-ZV'
            l = language.split('-')[0]
            language = 'en-US' # fallback if no other is found
            if l in self.manuals:
                language = l
            else:
                # Prefer 'en-US' before any other English dialect
                if l == 'en' and 'en-US' in self.manuals:
                    language = 'en-US'
                else:
                    # If there is none try to find
                    # any other 'xy-*' language
                    l += '-'
                    for lang in sorted(self.manuals.keys()):
                        if lang.startswith(l):
                            language = lang
                            break
            req.redirect(req.href.watchlist('manual',language))

        try:
            f = open(self.manuals[language], 'r')
            text = to_unicode( f.read() )
        except Exception as e:
            raise HTTPNotFound(e)

        wldict = dict(
                format_text=lambda text: format_to_html(self.env, Context.from_request(req), text),
                text=text)
        return ("watchlist_manual.html", wldict, "text/html")


    def handle_attachment(self, req, path):
        path = path[ len('attachments') : ].strip('/')
        dir = resource_filename('tracwatchlist', 'manuals/attachments')
        filename = os.path.join(dir, path)
        if os.path.isfile(filename):
            req.send_file(filename)
        else:
            raise HTTPNotFound(path)


# EOF
