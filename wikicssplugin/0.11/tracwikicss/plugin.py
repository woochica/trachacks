""" WikiCss Plug-in file

    Copyright (c) 2008 Martin Scharrer <martin@scharrer-online.de>
    This is Free Software under the BSD or GPL v3 or later license.
    $Id$
"""

__revision = r'$Rev$'[6:-2]
__date     = r'$Date$'[7:-2]
__author   = r'$Author$'[9:-2]
__url      = r'$URL$'[6:-2]

from  trac.core        import  *
from  trac.web.chrome  import  add_stylesheet
from  trac.web.api     import  IRequestFilter, IRequestHandler, RequestDone
from  trac.util.text   import  to_unicode

class WikiCssPlugin (Component):
    """ This Trac plug-in implements a way to use a wiki page as CSS file
    """
    implements ( IRequestHandler, IRequestFilter )


   # Init
    def __init__(self):
        self.wikipage = self.env.config.get('wikicss', 'wikipage')
        if not self.wikipage:
            self.log.error("WikiCss: Wiki page not configured.")


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
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute( \
                "SELECT text FROM wiki WHERE name=%s " \
                "ORDER BY version DESC;", (self.wikipage,) )
            content = cursor.fetchone()
            if not content:
                raise Exception("WikiCss: Configured wiki page '%s' doesn't exits." % self.wikipage)
            while isinstance(content,tuple) or isinstance(content,list):
                content = content[0]
            req.send(to_unicode(content), content_type='text/css', status=200)
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


