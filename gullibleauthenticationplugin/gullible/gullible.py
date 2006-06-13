# Voluntary Identities
# Gullible ID
# You are who you say you are
# Hello my name is Hector Petelbaum

import time
import cgi
from trac.core import *
from trac.web.chrome import INavigationContributor
from trac.web.main import IRequestHandler
from trac.util import escape, Markup
from trac.web.api import IAuthenticator, IRequestHandler

class UserbaseModule(Component):
    implements(INavigationContributor, IRequestHandler)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
		return 'authme'
     
		
           
    def get_navigation_items(self, req):
		if req.authname and req.authname == 'anonymous':
			req.authname = 'Hector Petelbaum'
		yield 'metanav', 'authme', Markup('''<FORM name="authme" action="/trac/authme" method="get">Hello My Name is:
			<INPUT type="text" name="name" value="%s" onblur="if(this.value==''){this.value='Hector Petelbaum'} else{document.authme.submit()}" onfocus="if(this.value=='Hector Petelbaum'){this.value=''}">
		    
		 </FORM>
		'''
		% req.authname)

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/authme'
    
    def process_request(self, req):
		#get the username from the get.
		form = cgi.FieldStorage()
		username = form['name'].value
		remote_user = username
		
		#set the authentication cookie
		def hex_entropy(bytes=32):
		    import md5
		    import random
		    return md5.md5(str(random.random() + time.time())).hexdigest()[:bytes]
		
		cookie = hex_entropy()
		db = self.env.get_db_cnx()
		cursor = db.cursor()
		cursor.execute("INSERT INTO auth_cookie (cookie,name,ipnr,time) " "VALUES (%s, %s, %s, %s)", (cookie, remote_user, req.remote_addr, int(time.time())))
		db.commit()

		req.authname = remote_user
		req.outcookie['trac_auth'] = cookie
		req.outcookie['trac_auth']['path'] = self.env.href()
		
		"""Redirect the user back to the URL she came from."""
		referer = req.get_header('Referer')
		if referer and not referer.startswith(req.base_url):
			referer = None
		req.redirect(referer or self.env.abs_href())
