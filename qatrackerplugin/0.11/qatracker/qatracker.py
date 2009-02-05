# QATracker plugin for TRAC 0.11

import re

from genshi.builder import tag

from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider, \
		add_stylesheet
from trac.ticket import Milestone, Ticket
from trac.ticket.roadmap import get_tickets_for_milestone
from trac.util import parse_date

class QATrackerPlugin(Component):
	implements(INavigationContributor, IRequestHandler, ITemplateProvider)

	#--------------------------------------------------------------------------

	# INavigationContributor methods
	def get_active_navigation_item(self, req):
		return 'qatracker'
	
	def get_navigation_items(self, req):
		yield ('mainnav', 'qatracker',
			   tag.a('QA Tracker', href=req.href.qatracker()))

	#--------------------------------------------------------------------------

	# IRequestHandler methods
	def match_request(self, req):
		return re.match(r'/qatracker(?:_trac)?(?:/.*)?$', req.path_info)

	def process_request(self, req):

		# This tuple is for Genshi (template_name, data, content_type)
		# Without data the Trac layout will not appear.
		data = {}

		# Layout for QA Tracker
		add_stylesheet(req, 'qa/css/qatracker.css')

		if req.method.upper() != 'POST':

			"""
			User enters data into the qatracker.html form to setup the new test run
			"""

			# milestones
			milestones = self._find_milestones()
			if milestones and len(milestones) > 0:
				data['milestones'] = [x for x in milestones]

			# usernames
			usernames = self._find_usernames()
			if usernames and len(usernames) > 0:
				data['usernames'] = [x for x in usernames]

			return 'qatracker.html', data, None

		###############################
		#  Processing a POST request  #
		###############################

		# 1. Are there errors?  If so, bail.
		errors = req.args.get('errors')
		if errors and len(errors) > 0:
			# TO-DO, do a meaningful redirect
			req.redirect(req.href.admin())

		# 2. Cool, we're supposedly golden
		errors = {}
		action = None

		# 3. Parse the POST arguments
		action1 = req.args.get('action1')
		action2 = req.args.get('action2')
		if action1 and action1 == "create":
			action = "create"
			newRun = self.validate_args(req.args.get('newrun'))
			due    = self.validate_args(req.args.get('duedate'), parse_date)
			assign = self.validate_args(req.args.get('assign1'))
			desc   = self.validate_args(req.args.get('description'))
			master = self.validate_args(req.args.get('masterplan1'))
		elif action2 and action2 == "change":
			action  = "change"
			current = self.validate_args(req.args.get('currentrun'))
			master  = self.validate_args(req.args.get('masterplan2'))
			assign  = self.validate_args(req.args.get('assign2'))
		else:
			errors['action'] = "Unknown form action"

		# 4. If we're doing a create, sanatize the new test run's name
		if action == "create":
			if not newRun:
				errors['newRun'] = "Missing Name for the new Test Run"
			elif len(newRun.strip()) < 1:
				errors['newRun'] = "Invalid Name for the new Test Run"
			elif "test run" not in newRun.lower():
				newRun = "%s Test Run" % newRun

		# 5. check for errors
		# TO-DO, add redirect to error page if we have errors

		# 6. Set the milestone properties
		if action == "create":
			self._create_milestone(newRun, due, desc)
			milestone = newRun
		elif action == "change":
			milestone = current

		# 7. Find all the test cases in the Master Test Plan
		db = self.env.get_db_cnx()
		#self._delete_tickets_from_milestone(db, "Useless Test Cases")
		tickets = get_tickets_for_milestone(self.env, db, master)
		self.env.log.info("Found %d tickets in milestone %s" % (len(tickets), master))

		# 8. Clone each ticket from the master into the new test run
		for t in tickets:
			status    = t['status']
			component = t['component']
			id        = t['id']
			if status.lower() == 'closed':
				self.env.log.info("Skipping ticket %d (status == %s)" % (id, status))
				continue
			self._clone_testcase(db, id, status, milestone, assign)

		# 9. Redirect to the the milestone roadmap
		req.redirect(req.href('milestone', milestone))

		# Done with POST

		# Should never get here, but just in case
		return 'qatracker.html', data, None

	#--------------------------------------------------------------------------

	# ITemplateProvider methods
	# Used to add the plugin's templates and htdocs 
	def get_templates_dirs(self):
		from pkg_resources import resource_filename
		return [resource_filename(__name__, 'templates')]

	#--------------------------------------------------------------------------

	def get_htdocs_dirs(self):
		"""Return a list of directories with static resources (such as style
		sheets, images, etc.)

		Each item in the list must be a `(prefix, abspath)` tuple. The
		`prefix` part defines the path in the URL that requests to these
		resources are prefixed with.

		The `abspath` is the absolute path to the directory containing the
		resources on the local file system.
		"""
		from pkg_resources import resource_filename
		return [('qa', resource_filename(__name__, 'htdocs'))]

	#--------------------------------------------------------------------------

	# Internal helper functions
	def _find_milestones(self):
		"""Return a string list of Milestone names
		
		A smarter approach would return a dictionary of milestones:
		key = name
		value = tuple (name, due, completed, description)
		"""

		return [ "%s" % m.name for m in Milestone.select(self.env) ]

	#--------------------------------------------------------------------------

	def _find_usernames(self):
		"""Return a string list of Usernames --- known users who have actually
		signed into this Trac project.
		
		A smarter approach would be a dictionary of usernames:
		key = username
		value = tuple (username, name, email)
		"""

		return sorted([ "%s" % username for username, name, email in self.env.get_known_users() ])

	#--------------------------------------------------------------------------

	def validate_args(self, value, formatter=None):
		if not value:
			return None
		value = value.strip()
		if formatter:
			return formatter(value)
		return value

	#--------------------------------------------------------------------------

	def _create_milestone(self, name, duedate, description):
		m = Milestone(self.env)
		m.name = name
		m.description = description
		if duedate:
			if isinstance(duedate, type("")):
				m.due = parse_date(duedate)
			else:
				m.due = duedate
		m.insert()

	#--------------------------------------------------------------------------

	def _clone_testcase(self, db, id, status, milestone, assign=None):
		self.env.log.info("Cloning ticket %d (status == %s)" % (id, status))
		ticket_new = Ticket(self.env, db=db)
		ticket_old = Ticket(self.env, tkt_id=id, db=db)
		for k,v in ticket_old.values.items():
			self.env.log.debug("id: %d\tkey: %s\t\tvalue: %s" % (id,k,v))
			ticket_new.values[k] = ticket_old.values[k]
			if assign and len(assign) > 0:
				ticket_new['owner'] = assign.strip()
		ticket_new.values['milestone'] = milestone
		ticket_new.insert()
		for k,v in ticket_new.values.items():
			self.env.log.info("%s\t%s" % (k, v))

	#--------------------------------------------------------------------------

	def _clone_testplan(self, milestone):
		pass

	#--------------------------------------------------------------------------

	def _delete_tickets_from_milestone(self, db, milestone):
		tickets = get_tickets_for_milestone(self.env, db, milestone)
		for t in tickets:
			id = t['id']
			ticket = Ticket(self.env, tkt_id=id, db=db)
			ticket.delete()