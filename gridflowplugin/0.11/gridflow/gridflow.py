# This Trac plugin is derived from other Trac components plus
# original code.
#
# Copyright (c) 2003-2008 Edgewall Software and contributors.
# Copyright (c) 2009 David Champion <dgc@uchicago.edu>.
#
# This code was inspired by Zach Miller's Gridmodify plugin, which is
# marked as 'Copyright (c) 2008 Zach Miller and Abbywinters.com.' Most
# of that code was actually copied verbatim from Trac itself, so I do
# not believe that any abbywinters.com copyright claim would be valid
# for this product. However, if this proves incorrect, I will gladly
# update the copyright notice or change the code.

from datetime import datetime 
import trac
import trac.ticket
import trac.ticket.web_ui
from trac.core import *
from trac.perm import IPermissionRequestor        
from trac.ticket import TicketSystem
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_script
from trac.web.main import IRequestHandler
from trac.ticket.notification import TicketNotifyEmail
from trac.ticket.model import Ticket
from trac.ticket.api import ITicketActionController
import trac.util
import trac.util.datefmt
import genshi
import genshi.builder
import genshi.path
from genshi.filters.transform import Transformer


class GridFlowPlugin(Component):
	implements(IPermissionRequestor, IRequestHandler,
			   ITemplateProvider, ITemplateStreamFilter,
	           ITicketActionController)

	# from trac.ticket.web_ui
	def _get_action_controllers(self, req, ticket, action):
		'''Generator yielding the controllers handling the given `action`'''
		for controller in TicketSystem(self.env).action_controllers:
			actions = [a for w,a in
					   controller.get_ticket_actions(req, ticket)]
			if action in actions:
				yield controller


	# IPermissionRequestor methods
	def get_permission_actions(self):
		yield 'TICKET_GRID_WORKFLOW'


	# ITemplateProvider methods
	def get_htdocs_dirs(self):
		from pkg_resources import resource_filename
		return [('gridflow', resource_filename(__name__, 'htdocs'))]

	def get_templates_dirs(self):
		from pkg_resources import resource_filename
		return []


	# ITicketActionController methods
	# Pilfered liberally from trac.ticket.web_ui
	def get_ticket_changes(self, req, ticket, action):
		field_changes = {}
		problems = []

		for field, value in ticket._old.iteritems():
			field_changes[field] = {'old': value,
			                        'new': ticket[field],
			                        'by': 'user'}

		for ctlr in self._get_action_controllers(req, ticket, action):
			#original#cname = ctlr.__class__.__name__
			cname = '%s <%s>' % (self.__class__.__name__,
			                     ctlr.__class__.__name__)
			changes = ctlr.get_ticket_changes(req, ticket, action)
			for key in changes.keys():
				old = ticket[key]
				new = changes[key]
				# Check for conflicts between controllers.  (If a change
				# to this field was already made, remark upon it.)
				if key in field_changes:
					prev_new = field_changes[key]['new']
					prev_by  = field_changes[key]['by']
					if prev_new != new and prev_by:
						problems.append('%s changes "%s" to "%s", but '
						                '%s changed it to "%s".' %
						                (cname, key, new, prev_by, prev_new))
				field_changes[key] = {'old': old, 'new': new, 'by': cname}

		# Remove 'changes' which change nothing
		for key, item in field_changes.items():
			if item['old'] == item['new']:
				del field_changes[key]

		return field_changes, problems


	# IRequestHandler methods
	def match_request(self, req):
		'''Detect GridFlow AJAX callbacks.'''
		return req.path_info.startswith('/gridflow/ajax')


	def _process_request(self, req):
		'''Intercept and execute GridFlow AJAX callbacks.'''
		if not req.perm.has_permission('TICKET_ADMIN') and \
		   not req.perm.has_permission('TICKET_GRID_WORKFLOW'):
			raise Exception('Permission denied')

		id = req.args.get('id')
		action = req.args.get('action')
		ticket = Ticket(self.env, id)
		ts = TicketSystem(self.env)

		validActions = ts.get_available_actions(req, ticket)
		if action not in validActions:
			req.send_response(500)
			req.send_header('Content-Type', 'text/plain')
			req.end_headers()
			req.write('"%s" is not a valid action for #%d\n' %
			          (action, id))
			return

		changes, problems = self.get_ticket_changes(req, ticket, action)
		if problems:
			req.send_response(500)
			req.send_header('Content-Type', 'text/plain')
			req.end_headers()
			req.write('Problems: %s\n' % problems)
			return


		self._apply_ticket_changes(ticket, changes)
		valid, reasons = self._validate_ticket(req, ticket)
		if not valid:
			req.send_response(500)
			req.send_header('Content-Type', 'text/plain')
			req.end_headers()
			req.write('Changes not valid:\n')
			for reason in reasons:
				req.write('* ' + reason + '\n')
			return

		self._save(req, ticket, action)
		req.send_response(200)
		req.send_header('Content-Type', 'text/plain')
		req.end_headers()
		req.write('OK')
		return


	def _apply_ticket_changes(self, ticket, changes):
		self.env.log.debug('Applying changes')
		for change in changes:
			self.env.log.debug('Applying change: %s = %s' %
			                   (change, changes[change]['new']))
			ticket[change] = changes[change]['new']


	# Nicked in large part from trac.ticket.web_ui
	def _validate_ticket(self, req, ticket):
		valid = True
		resource = ticket
		reasons = []

		# If changes made to existing ticket, require change permission
		if ticket.exists and ticket._old:
			allowed = False
			perms = req.perm(resource)
			if req.perm.has_permission('TICKET_ADMIN'):
				allowed = True
			elif req.perm.has_permission('TICKET_CHGPROP'):
				allowed = True
			elif req.perm.has_permission('TICKET_GRID_WORKFLOW'):
				allowed = True
			if not allowed:
				reasons.append('No permission to change ticket fields.')
				valid = False

		# Check for race conflict
		# TODO: in filter_stream, store ticket.time_changed in a js array,
		# then add a ticket's time_changed as value 'ts' to its ajax callback.
		# Until this works, this validation is useless.
		if ticket.exists and (ticket._old):
			ts = req.args.get('ts')
			if ts and ts != str(ticket.time_changed):
				reasons.append('Cannot save changes: this ticket '
				               'was modified (%s != %s)' %
				               (req.args.get('ts'), str(ticket.time_changed)))
				valid = False

		# Validate exclusive option types
		for field in ticket.fields:
			if 'options' not in field:
				continue
			name = field['name']
			if name == 'status':
				# exempt
				continue
			if name in ticket.values and name in ticket._old:
				if ticket[name] not in field['options']:
					reasons.append('"%s" is not a valid value for '
					               'the "%s" field.' % (ticket[name], name))
					valid = False
				elif not field.get('optional', False):
					reasons.append('Field "%s" must be set.' % name)
					valid = False

		return valid, reasons


	# Largely cribbed from trac.ticket.web_ui
	def _save(self, req, ticket, action):
		self.env.log.debug('Saving changes')

		# Remember action controllers for side effects, because saving
		# ticket changes could alter this query.
		side_effects = list(self._get_action_controllers(req, ticket, action))

		now = datetime.now(trac.util.datefmt.utc)
		if ticket.save_changes(trac.util.get_reporter_id(req, 'author'),
		                       req.args.get('comment'), when=now):
			try:
				tn = TicketNotifyEmail(self.env)
				tn.notify(ticket, newticket=False, modtime=now)
			except Exception, e:
				self.log.exception('Failure sending notification on change ' +
				                   'to #%s: %s' % (ticket.id, e))

		for ctlr in side_effects:
			self.env.log.debug('Side effect for %s' % ctlr.__class__.__name__)
			ctlr.apply_action_side_effects(req, ticket, action)

		return


	def process_request(self, req):
		'''Intercept and execute GridFlow AJAX callbacks (with error trap)'''
		try:
			self._process_request(req)
		except Exception, e:
			req.send_response(500)
			req.send_header('Content-Type', 'text/plain')
			req.end_headers()
			req.write("Oops...\n");
			import traceback;
			req.write(traceback.format_exc()+"\n");
			self.env.log.info(traceback.format_exc())


	# ITemplateStreamFilter methods
	def filter_stream(self, req, method, filename, stream, formdata):
		'''Add workflows to query/report output'''
		if filename != 'query.html' and filename != 'report_view.html':
			return stream
		if not (req.perm.has_permission('TICKET_ADMIN') or
		        req.perm.has_permission('TICKET_GRID_WORKFLOW')):
			return stream

		ts = TicketSystem(self.env)

		add_script(req, 'gridflow/gridflow.js')

		html = stream.render()
		js = ''
		tickets = []

		copy = genshi.XML(html)
		nodes = genshi.path.Path('//td[contains(@class, "ticket")]//a/text()')
		tickets += [int(a[1][1:]) for a in nodes.select(copy)]

		copy = genshi.XML(html)
		nodes = genshi.path.Path('//td[contains(@class, "id")]//a/text()')
		tickets += [int(a[1][1:]) for a in nodes.select(copy)]

		copy = genshi.XML(html);
		tktDict = {}
		for tno in tickets:
			tktDict[tno] = {'labels': [], 'widgets': [], 'actions': []}
			tkt = trac.ticket.Ticket(self.env, tno)
			actions = ts.get_available_actions(req, tkt)
			for action in actions:
				for controller in self._get_action_controllers(req, tkt, action):
					(label, widget, hint) = controller.render_ticket_action_control(req, tkt, action)
					tktDict[tno]['actions'].append(action)
					tktDict[tno]['labels'].append(label)
					tktDict[tno]['widgets'].append(widget.generate().render())

		js += 'tktDict = ' + repr(tktDict).replace(", u'", ", '").replace("[u'", "['") + ';\n'
		js += 'baseURL = "%s";\n' % req.base_url

		script = genshi.builder.tag.script(js, type="text/javascript")
		xpath = '//head'
		copy |= Transformer(xpath).append(script)
		return copy
