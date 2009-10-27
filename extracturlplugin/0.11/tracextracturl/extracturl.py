""" Copyright (c) 2008 Martin Scharrer <martin@scharrer-online.de>
    v0.1 - Oct 2008
    This is Free Software under the GPL v3!
""" 
from trac.core import *

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int(r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]


def extract_url (env, context, wikilink, raw=False):
    """Extracts an URL from an Wiki link, e.g. to used in macro produced HTML code.

Website: http://trac-hacks.org/wiki/ExtractUrlPlugin

`$Id$`

== Description ==
Returns an (possible relative) URL which can be used in HTML code.

If `raw` is true the returned link will point to a downloadable
version of the linked resource otherwise the same link is returned
which would be used in the resulting Wiki page.

The raw links are also usable as online resouces, e.g. if the link target
is to be used as input for a flash application etc.

== Example ==
Inside a Trac macro called from the wiki page 'ExamplePage' of project
'project1' on a multi-project trac server:
{{{
    extract_url(self.env, formatter, 'attachment:file.js', True)
}}}
will return `/project1/raw-attachment/wiki/ExamplePage/file.js`,
which could be directly accessed by the browser inside some javascript 
or flash HTML object code produced by the macro.
    """
    from genshi.builder import Element, Fragment
    from trac.wiki.formatter import extract_link

    if not wikilink:
        return ''

    link = extract_link(env, context, '[' + wikilink + ' x]')
    #env.log.debug("link = " + str(link.__class__) + ' ' + str(link))

    if isinstance(link, Element):
        href = link.attrib.get('href')
        #env.log.debug("href1 = " + href)
    elif isinstance(link, Fragment):
        link = link.children[0]
        href = link.attrib.get('href')
        #env.log.debug("href2 = " + href)
    else:
        href = None

    if not href:
        return ''

    if raw:
        # rewrite URL to point to downloadable/exportable/raw version of the 
        # linked resource

        # Remove existing project URL part for later string search
        base_path = context.req.base_path
        if base_path and href.startswith(base_path):
            # href relative to base path
            rhref = href[len(base_path):]
        else:
            rhref = href

        # For browser links add the 'format=raw' URL parameter.
        # The alternative '/export' target isn't used because a revision number
        # would be needed.
        if rhref.startswith('/browser/'):
            if rhref.find('?') == -1:
                # If no other parameter exists, simply append:
                href += r'?format=raw'
            else:
                # Otherwise add to existing parameters if this one doesn't
                # exists yet:
                if href.find(r'?format=') == -1 and href.find(r'&format=') == -1:
                    href += r'&format=raw'
        # Change 'attachment' links to 'raw-attachment' links:
        elif rhref.startswith('/attachment/'):
            href = href.replace('/attachment/','/raw-attachment/', 1)
        # All other link types should be already fine for file export (if
        # applicable)
    return href

