""" WikiCss Plug-in file

    Copyright (c) 2008 Martin Scharrer <martin@scharrer-online.de>
    This is Free Software under the BSD or GPL v3 or later license.
    $Id$
"""

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]

from  trac.core        import  *
from  trac.web.chrome  import  add_stylesheet
from  trac.web.api     import  IRequestFilter, IRequestHandler, RequestDone
from  trac.util.text   import  to_unicode
from  trac.wiki.model  import  WikiPage
from  trac.config      import  Option

class WikiCssPlugin (Component):
    """ This Trac plug-in implements a way to use a wiki page as CSS file
    """
    implements ( IRequestHandler, IRequestFilter )
    wikipage = Option('wikicss', 'wikipage')

   # IRequestHandler methods
    def match_request(self, req):
        if self.wikipage:
            return req.path_info == '/wikicss.css'
        else:
            return False

    def process_request(self, req):
        try:
            if req.path_info != '/wikicss.css':
                raise Exception ("Unsupported path requested!")
            if not self.wikipage:
                raise Exception ("WikiCss: Wiki page not configured.")

            wiki = WikiPage(self.env, self.wikipage)

            if not wiki.exists:
                raise Exception("WikiCss: Configured wiki page '%s' doesn't exits." % self.wikipage)

            req.send( wiki.text, content_type='text/css', status=200)
        except RequestDone:
            pass
        except Exception, e:
            self.log.error(e)
            req.send_response(404)
            req.end_headers()
        raise RequestDone


   # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if self.wikipage:
            add_stylesheet( req, '/wikicss.css', mimetype='text/css' )
        return (template, data, content_type)


