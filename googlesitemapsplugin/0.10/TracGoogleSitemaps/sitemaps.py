"""
$Id$
$HeadURL$

Copyright (c) 2006 Harald Radi. All rights reserved.

Google Sitemaps Plugin
"""



__revision__  = '$LastChangedRevision$'
__id__        = '$Id$'
__headurl__   = '$HeadURL$'
__docformat__ = 'restructuredtext'
__version__   = '0.1'


import fnmatch
from trac.core import *
from trac.web.main import IRequestHandler
from trac.config import Option


class GoogleSitemapsModule(Component):
    implements(IRequestHandler)

    pagename = Option('googlesitemaps', 'pagename', '', 'Name of the Google Sitemaps confirmation page (e.g. googleeb3689b3689b3689.html).')

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/sitemap') or req.path_info.startswith('/' + self.pagename)
    

    def process_request(self, req):
    	if req.path_info.startswith('/sitemap'):
            db = self.env.get_db_cnx()
	    cursor = db.cursor()
	    cursor.execute('SELECT DISTINCT name FROM wiki ORDER BY name')
	    
            req.send_response(200)
	    req.send_header('Content-Type', 'text/xml')
	    req.end_headers()

            req.write("""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.google.com/schemas/sitemap/0.84">
""")

            for row in cursor.fetchall():
	    	req.write('  <url>\n')
		req.write('    <loc>' + req.base_url + self.env.href.wiki() + '/' + row[0] + '</loc>\n')
		req.write('  </url>\n')

	    req.write('</urlset>')

        elif req.path_info.startswith('/' + self.pagename):
            req.send_response(200)
            req.send_header('Content-Type', 'text/plain')
            req.end_headers()
            req.write('Hello Google!')

        else:
	    req.send_response(404)
	    req.end_headers()

