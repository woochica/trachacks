#
#
#

import re

from genshi.builder import tag

from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider

from datetime import datetime, time, timedelta
from trac.util.datefmt import to_timestamp, utc

# ************************
DEFAULT_DAYS_BACK = 30*6 
DEFAULT_INTERVAL = 30
# ************************

class TicketStatsPlugin(Component):
	implements(INavigationContributor, IRequestHandler, ITemplateProvider)

	# ==[ INavigationContributor methods ]==

	def get_active_navigation_item(self, req):
		return 'ticketstats'

	def get_navigation_items(self, req):
		yield ('mainnav', 'ticketstats', 
			tag.a('Ticket Stats', href=req.href.ticketstats()))

	# ==[ Helper functions ]==
	def _get_num_closed_tix(self, from_date, at_date, req):
		'''
		Returns an integer of the number of close ticket
		events counted between from_date to at_date.
		'''
		status_map = {'new': 0,
			      'reopened': 0,
			      'assigned': 0,
			      'closed': 1,
			      'edit': 0}

		count=0

		db = self.env.get_db_cnx()
		cursor = db.cursor()
	
		# TODO clean up this query
		cursor.execute("SELECT t.id, tc.field, tc.time, tc.oldvalue, tc.newvalue, t.priority FROM ticket_change tc, enum p INNER JOIN ticket t ON t.id = tc.ticket AND tc.time > %s AND tc.time <= %s WHERE p.name = t.priority AND p.type = 'priority' ORDER BY tc.time" % (to_timestamp(from_date), to_timestamp(at_date)))

		for id, field, time, old, status, priority in cursor:
			if field == 'status':
				if status in ('new', 'assigned', 'reopened', 'closed', 'edit'):
					count+=status_map[status]

		return count


	def _get_num_open_tix(self, at_date, req):
		'''
		Returns an integer of the number of tickets
		currently open on that date.
		'''
		status_map = {'new': 0,
			      'reopened': 1,
			      'assigned': 0,
			      'closed': -1,
			      'edit': 0}

		count=0

		db = self.env.get_db_cnx()
		cursor = db.cursor()
	
		# TODO clean up this query
		cursor.execute("SELECT t.type AS type, owner, status, time AS created FROM ticket t, enum p WHERE p.name = t.priority AND p.type = 'priority' AND created <= %s" % to_timestamp(at_date))

		for rows in cursor:
			count += 1

		# TODO clean up this query
		cursor.execute("SELECT t.id, tc.field, tc.time, tc.oldvalue, tc.newvalue, t.priority FROM ticket_change tc, enum p INNER JOIN ticket t ON t.id = tc.ticket AND tc.time > 0 AND tc.time <= %s WHERE p.name = t.priority AND p.type = 'priority' ORDER BY tc.time" % to_timestamp(at_date))

		for id, field, time, old, status, priority in cursor:
			if field == 'status':
				if status in ('new', 'assigned', 'reopened', 'closed', 'edit'):
					count+=status_map[status]

		return count


	# ==[ IRequestHandle methods ]==

	def match_request(self, req):
		return re.match(r'/ticketstats(?:_trac)?(?:/.*)?$', req.path_info)

	def process_request(self, req):
		
		if not None in [req.args.get('end_date'), req.args.get('start_date'), req.args.get('resolution')]:
			# form submit
			grab_at_date = req.args.get('end_date')
			grab_from_date = req.args.get('start_date')
			grab_resolution = req.args.get('resolution')

			# validate inputs
			if None in [grab_at_date, grab_from_date]:
				raise TracError('Please specify a valid range.')

			if None in [grab_resolution]:
				raise TracError('Please specify the graph interval.')
			
			if 0 in [len(grab_at_date), len(grab_from_date), len(grab_resolution)]:
				raise TracError('Please ensure that all fields have been filled in.')

			if not grab_resolution.isdigit():
				raise TracError('The graph interval field must be an integer, days.')

			# TODO: I'm letting the exception raised by 
			#	strptime() appear as the Trac error.
			#	Maybe a wrapper should be written.

			at_date = datetime.strptime(grab_at_date, "%m/%d/%Y")
			at_date = datetime.combine(at_date, time(11,59,59,0,utc)) # Add tzinfo

			from_date = datetime.strptime(grab_from_date, "%m/%d/%Y")
			from_date = datetime.combine(from_date, time(0,0,0,0,utc)) # Add tzinfo

			graph_res = int(grab_resolution)

		else:
			global DEFAULT_DAYS_BACK 
			global DEFAULT_INTERVAL

			# default data
			todays_date = datetime.today()
			at_date = datetime.combine(todays_date,time(11,59,59,0,utc))
			from_date = at_date - timedelta( DEFAULT_DAYS_BACK )
			graph_res = DEFAULT_INTERVAL
			
		count = []

		# Calculate 0th point 
		last_date = from_date - timedelta(graph_res)
		last_num_open = self._get_num_open_tix(last_date, req)

		# Calculate remaining points
		for cur_date in daterange(from_date, at_date, graph_res):
			num_open = self._get_num_open_tix(cur_date, req)
			num_closed = self._get_num_closed_tix(last_date, cur_date, req)
			datestr = cur_date.strftime("%m/%d/%Y") 
			if graph_res != 1:
				datestr = "%s thru %s" % (last_date.strftime("%m/%d/%Y"), datestr) 
			count.append( {'date'  : datestr,
				       'new'   : num_open - last_num_open + num_closed,
				       'closed': num_closed,
				       'open'  : num_open })
			last_num_open = num_open
			last_date = cur_date

		data = {'chart_data': count}
		
		req.hdf['ticket_data'] = data
		req.hdf['start_date'] = from_date.strftime("%m/%d/%Y")
		req.hdf['end_date'] = at_date.strftime("%m/%d/%Y")
		req.hdf['resolution'] = str(graph_res)

		return 'greensauce.cs', None

	def get_templates_dirs(self):
		from pkg_resources import resource_filename
		return [resource_filename(__name__, 'templates')]

def daterange(begin, end, delta = timedelta(1)):
    """Stolen from: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/574441

    Form a range of dates and iterate over them.  

    Arguments:
    begin -- a date (or datetime) object; the beginning of the range.
    end   -- a date (or datetime) object; the end of the range.
    delta -- (optional) a timedelta object; how much to step each iteration.
             Default step is 1 day.
             
    Usage:

    """
    if not isinstance(delta, timedelta):
        delta = timedelta(delta)

    ZERO = timedelta(0)

    if begin < end:
        if delta <= ZERO:
            raise StopIteration
        test = end.__gt__
    else:
        if delta >= ZERO:
            raise StopIteration
        test = end.__lt__

    while test(begin):
        yield begin
        begin += delta




