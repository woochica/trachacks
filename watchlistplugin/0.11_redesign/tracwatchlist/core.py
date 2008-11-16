"""
 Watchlist Plugin for Trac
 Copyright (c) November 2008  Martin Scharrer <martin@scharrer-online.de>
 This is Free Software under the BSD license.
"""
from  trac.core        import  TracError
from  genshi.builder   import  tag

class WatchlistError(TracError):
    show_traceback = False
    title = 'Watchlist Error'

    def __init__(self, message):
        Exception.__init__(self, tag.div(message, class_='system-message') )

