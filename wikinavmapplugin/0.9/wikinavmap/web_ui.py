from trac.core import *
from trac.util import Markup
from trac.web import IRequestHandler
from trac.perm import IPermissionRequestor
from trac.config import Option
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_script, add_stylesheet
from trac.wiki.formatter import wiki_to_html
from StringIO import StringIO
import time
import re

class WikiNavMapPlugin(Component):
	implements(INavigationContributor, IRequestHandler, ITemplateProvider, IPermissionRequestor)

	#Default Colour for nodes red|green|blue|black|purple|yellow|aqua
	default_base_colour = Option('wikinavmap', 'default_base_colour', 'red')
	
	#Default number of node colour gradients (1-5)
	default_colour_no = Option('wikinavmap', 'default_colour_no', '5')

	#Default whether to show tickets
	default_show_tickets = Option('wikinavmap', 'default_show_tickets', 'on')

	#Default tickets to show all|active|mine|myactive|user|useractive
	default_ticket_filter = Option('wikinavmap', 'default_ticket_filter', 'myactive')
	
	#If default_ticket_filter is user or useractive then this is the username to use
	default_t_username = Option('wikinavmap', 'default_t_username', '')
	
	#Default whether to show wiki pages
	default_show_wiki = Option('wikinavmap', 'default_show_wiki', 'on')
	
	#Default wiki pages to show all|mine|others|user
	default_wiki_filter = Option('wikinavmap', 'default_wiki_filter', 'all')
	
	#If default_wiki_filter is user then this is the username to use
	default_w_username = Option('wikinavmap', 'default_w_username', '')
	
	# INavigationContributor methods
	def get_active_navigation_item(self, req):
		return 'wikinavmap'
	
	
	def get_navigation_items(self, req):
		if not (req.perm.has_permission('MILESTONE_VIEW') and req.perm.has_permission('WIKI_VIEW') and req.perm.has_permission('TICKET_VIEW')):
			return		
		yield 'mainnav', 'wikinavmap', Markup('<a href="%s?referer=%s&base_colour=%s&colour_no=%s&show_tickets=%s&ticket_filter=%s&t_username=%s&show_wiki=%s&wiki_filter=%s&w_username=%s">WikiNavMap</a>' % (req.href.navmap(), req.hdf.getValue('HTTP.PathInfo', 'None'), self.default_base_colour, self.default_colour_no, self.default_show_tickets, self.default_ticket_filter, self.default_t_username, self.default_show_wiki, self.default_wiki_filter, self.default_w_username))
	
	
	# IRequestHandler methods
	def match_request(self, req):
		return req.path_info == '/navmap'
	
	
	# IPermissionRequestor methods
	def get_permission_actions(self):
		return ['TICKET_VIEW','WIKI_VIEW','MILESTONE_VIEW']
	
	
	def process_request(self, req):
		req.perm.assert_permission('WIKI_VIEW')
		req.perm.assert_permission('MILESTONE_VIEW')
		req.perm.assert_permission('TICKET_VIEW')
		try: 
			req.args['helpmenu']
			add_stylesheet(req, 'common/css/wiki.css')
			return 'helpmenu.cs', 'text/html'		
		except:
			pass
		add_script(req, 'wikinavmap/js/prototype.js')
		add_script(req, 'wikinavmap/js/scriptaculous.js')
		add_script(req, 'wikinavmap/js/popup.js')
		add_script(req, 'wikinavmap/js/mapdata.js')
		add_script(req, 'wikinavmap/js/configuration.js')
		add_stylesheet(req, 'wikinavmap/css/map.css')
		#req.hdf['wikinavmap.map_html'] = self.map_html(req)
		wikinavmap = {'default_base_colour':self.default_base_colour, 'default_colour_no':self.default_colour_no, 'default_ticket_filter':self.default_ticket_filter, 'default_wiki_filter':self.default_wiki_filter}
		req.hdf['wikinavmap'] = wikinavmap
		# Get the users for the filter options w_username and t_username
		db = self.env.get_db_cnx()
		cursor = db.cursor()
		cursor.execute("SELECT DISTINCT author FROM wiki WHERE author!='' UNION SELECT DISTINCT owner FROM ticket WHERE owner!='' UNION SELECT DISTINCT reporter FROM ticket WHERE reporter!=''");
		users = []
		for row in cursor:
				users.append(row[0])
		req.hdf['users'] = users
		return 'wikinavmap.cs', 'text/html'
	
		
	def get_templates_dirs(self):
		"""Return the absolute path of the directory containing the provided
		ClearSilver templates.
		"""
		from pkg_resources import resource_filename
		return [resource_filename(__name__, 'templates')]
	
	
	def get_htdocs_dirs(self):
		from pkg_resources import resource_filename
		return [('wikinavmap', resource_filename(__name__, 'htdocs'))]
	



		
