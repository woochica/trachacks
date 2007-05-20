# -*- coding: utf-8 -*-

"""
This macro allows you to add <link> to <head>.
This allows you to for example insert an RSS feed for a page.

Author: Thomas Vander Stichele

Usage:

{{{
  [[HeadLink(rel, mimetype, URL, title)]]
}}}

Where:

rel::

  rel attribute (e.g., "alternate")

mimetype::

  the type of the link (e.g., "application/rss+xml")

URL::

  the URL of the link

title::

  the title of the link



Example:

{{{
[[HeadLink(alternate application/rss+xml http://thomas.apestaart.org/moap/releases.rss2 RSS 2.0 Release feed)]]
}}}

This inserts the following HTML code in the <head> section:

<link rel="alternate" href="http://thomas.apestaart.org/moap/releases.rss2" title="RSS 2.0 Release feed" type="application/rss+xml" />
  [[Color(red,This has a red background)]]
"""

from trac.util import escape

def execute(hdf, txt, env):
    # Currently hdf is set only when the macro is called
    # From a wiki page

    # FIXME: trac 0.11 will remove hdf and use Genshi for templating

    if not txt:
        raise IndexError('HeadLink expects 4 arguments: mime type href title')
    t = txt.split(' ', 3)
    if len(t) < 4:
        raise IndexError('HeadLink expects 4 arguments: mime type href title')
    rel, mimetype, href, title = t
    
    # see trac.web.chrome.add_link for this bit of code
    if hdf:
        link = {'href': href}
        if title:
            link['title'] = escape(title)
        if mimetype:
            link['type'] = mimetype
        idx = 0
        while hdf.get('chrome.links.%s.%d.href' % (rel, idx)):
            idx += 1
        hdf['chrome.links.%s.%d' % (rel, idx)] = link
