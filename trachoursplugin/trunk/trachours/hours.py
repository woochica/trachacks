# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Jeff Hammel <jhammel@openplans.org>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from genshi.builder import tag
from genshi.filters import Transformer
from trac.core import *
from trac.mimeview.api import Context
from trac.perm import IPermissionRequestor
from trac.ticket import Ticket
from trac.ticket.api import ITicketManipulator, TicketSystem
from trac.ticket.query import Query
from trac.util.datefmt import to_timestamp, utc
from trac.util.translation import _
from trac.web.api import IRequestHandler, ITemplateStreamFilter
from trac.web.chrome import (
    INavigationContributor, ITemplateProvider, add_ctxtnav,
    add_link, add_script, add_stylesheet, add_warning, prevnext_nav
)

from componentdependencies.interface import IRequireComponents
from tracsqlhelper import *
from multiproject import MultiprojectHours
from setup import SetupTracHours
from utils import get_all_users, get_date

from StringIO import StringIO
from datetime import datetime, timedelta
import calendar
import csv
import dateutil.parser
import re
import time


def query_to_query_string(query):
    """return a URL query string from a dictionary"""
    args = []
    for k, v in query.items():
        try:
            if isinstance(v, basestring):
                args.append((k, v))
            else:
                args.extend([(k, i) for i in v])
        except TypeError:
            args.append((k, v))
    args = "&".join(["%s=%s" % i for i in args])
    return args

### main class for TracHours

class TracHoursPlugin(Component):

    implements(IRequestHandler, 
               ITemplateStreamFilter, 
               INavigationContributor, 
               ITemplateProvider, 
               IPermissionRequestor, 
               ITicketManipulator,
               IRequireComponents)


    ###### class data
    date_format = '%B %d, %Y'     # XXX should go to api ?
    fields = [dict(name='id', label='Ticket'), #note that ticket_time id is clobbered by ticket id
              dict(name='seconds_worked', label='Hours Worked'),
              dict(name='worker', label='Worker'),
              dict(name='submitter', label='Work submitted by'),
              dict(name='time_started', label='Work done on'),
              dict(name='time_submitted', label='Work recorded on')]


    ###### API

    def tickets_with_hours(self):
        """return all ticket.ids with hours"""
        return set(get_column(self.env, 'ticket_time', 'ticket'))

    def update_ticket_hours(self, ids):
        """
        update the totalhours ticket field from the tracked hours information
        * ids: ticket ids (list)
        """

        results = get_all_dict(self.env, "select sum(seconds_worked) as t, ticket from ticket_time where ticket in (%s) group by ticket" % ",".join(map(str,ids)))

        #If no work has been logged for a ticket id, nothing will be returned for that id, but we want it to return 0
        for id in ids:
            id_ismember = False
            for result in results:
                if id == result['ticket']:
                    id_ismember = True
            if not id_ismember:
                results.append({'ticket':id, 't':0})

        update = "update ticket_custom set value=%s where name='totalhours' and ticket=%s"
        for result in results:
            formatted = "%8.2f" % (float(result['t']) / 3600.0)
            execute_non_query(self.env, update, formatted, result['ticket'])

    def get_ticket_hours(self, ticket_id, from_date=None, to_date=None, worker_filter=None):
        
        if not ticket_id:
            return []
        
        args = []
        if isinstance(ticket_id, int):
            where = "ticket = %s"
            args.append(ticket_id)
        else:
            # Note the lack of args.  This is because there's no way to do a placeholder for a list that I can see.
            where = "ticket in (%s)" % ",".join(map(str, ticket_id))

        if from_date:
            where += " and time_started >= %s"
            args.append(int(time.mktime(from_date.timetuple())))

        if to_date:
            where += " and time_started < %s"
            args.append(int(time.mktime(to_date.timetuple())))
            
        if worker_filter and worker_filter != '*any':
            where += " and worker = %s"
            args.append(worker_filter)

        sql = """select * from ticket_time where """ + where
        result = get_all_dict(self.env, sql, *args)

        return result

    def get_total_hours(self, ticket_id):
        """return total SECONDS associated with ticket_id""" 
        return sum([hour['seconds_worked'] for hour in self.get_ticket_hours(int(ticket_id))])


    def add_ticket_hours(self, tid, worker, seconds_worked, submitter=None, time_started=None, comments=''):
        """
        add hours to a ticket:
        * tid : id of the ticket
        * worker : who did the work on the ticket
        * seconds_worked : how much work was done, in seconds
        * submitter : who recorded the work, if different from the worker
        * time_started : when the work was begun (a Datetime object) if other than now
        * comments : comments to record
        """

        # prepare the data
        if submitter is None:
            submitter = worker
        if time_started is None:
            time_started = datetime.now()
            # FIXME: timestamps should be in UTC
            #time_started = datetime.now(utc)
        #time_started = to_utimestamp(time_started)
        time_started = int(time.mktime(time_started.timetuple()))
        comments = comments.strip()

        # execute the SQL
        sql = """insert into ticket_time(ticket, 
                                         time_submitted,
                                         worker,
                                         submitter,
                                         time_started,
                                         seconds_worked,
                                         comments) values 
(%s, %s, %s, %s, %s, %s, %s)"""
        execute_non_query(self.env, sql, tid, int(time.time()),
                          worker, submitter, time_started,
                          seconds_worked, comments)

        # update the hours on the ticket
        self.update_ticket_hours([tid])

    def delete_ticket_hours(self, tid):
        """Delete hours for a ticket.

        :param tid: id of the ticket
        """
        execute_non_query(self.env, """
            DELETE FROM ticket_time WHERE ticket=%s""", tid)

    ###### methods and attributes for trac Interfaces

    ### method for IRequireComponents
    def requires(self):
        return [SetupTracHours]


    ### method for IPermissionRequestor
    def get_permission_actions(self):
        """Return a list of actions defined by this component.
        
        The items in the list may either be simple strings, or
        `(string, sequence)` tuples. The latter are considered to be "meta
        permissions" that group several simple actions under one name for
        convenience.
        """
        return ['TICKET_ADD_HOURS']

    # IRequestHandler methods

    def match_request(self, req):
        """Return whether the handler wants to process the given request."""
        path = req.path_info.rstrip('/')
        if not path.startswith('/hours'):
            return False
        if path == '/hours':
            return True
        if path.startswith('/hours/query'):
            return True
        ticket_id = path.split('/hours/', 1)[-1]
        try:
            int(ticket_id)
            return True
        except ValueError:
            return False

    def process_request(self, req):
        """Process the request. For ClearSilver, return a (template_name,
        content_type) tuple, where `template` is the ClearSilver template to use
        (either a `neo_cs.CS` object, or the file name of the template), and
        `content_type` is the MIME type of the content. For Genshi, return a
        (template_name, data, content_type) tuple, where `data` is a dictionary
        of substitutions for the template.

        For both templating systems, "text/html" is assumed if `content_type` is
        `None`.

        Note that if template processing should not occur, this method can
        simply send the response itself and not return anything.
        """
        path = req.path_info.rstrip('/')

        if path == '/hours':
            return self.process_timeline(req)
        
        if path.startswith('/hours/query'):
            return self.save_query(req)
        
        ### assume a ticket if the other handlers don't work
        return self.process_ticket(req)

    ### INavigationContributor methods

    def get_active_navigation_item(self, req):
        """This method is only called for the `IRequestHandler` processing the
        request.
        
        It should return the name of the navigation item that should be
        highlighted as active/current.
        """
        return 'hours'

    def get_navigation_items(self, req):
        """Should return an iterable object over the list of navigation items to
        add, each being a tuple in the form (category, name, text).
        """
        yield ('mainnav', 'hours',
               tag.a(_("Hours"), href=req.href.hours(), accesskey='H'))


    ### ITemplateProvider methods

    """Extension point interface for components that provide their own
    ClearSilver templates and accompanying static resources.
    """

    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        return []

    def get_templates_dirs(self):
        """Return a list of directories containing the provided template files."""
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]


    ### methods for ITicketManipulator

    def prepare_ticket(self, req, ticket, fields, actions):
        """Not currently called, but should be provided for future
        compatibility."""

    def validate_ticket(self, req, ticket):
        """Validate a ticket after it's been populated from user input.
        
        Must return a list of `(field, message)` tuples, one for each problem
        detected. `field` can be `None` to indicate an overall problem with the
        ticket. Therefore, a return value of `[]` means everything is OK."""

        # Check that 'estimatedhours' is a custom-field
        if ticket.get_value_or_default('estimatedhours') is None:
            msg = _("""The field is not defined. Please check your configuration.""")
            return [('estimatedhours', msg)]

        # Check that user entered a positive number
        if ticket['estimatedhours']:
            try:
                float(ticket['estimatedhours'])
            except ValueError:
                msg = _("Please enter a number for Estimated Hours")
                return [('estimatedhours', msg)]
            if float(ticket['estimatedhours']) < 0:
                msg = _("Please enter a positive value for Estimated Hours")
                return [('estimatedhours', msg)]
        else:
            ticket['estimatedhours'] = '0'

        return []


    ### method for ITemplateStreamFilter
    def filter_stream(self, req, method, filename, stream, data):
        """
        filter hours and estimated hours fields to have them 
        correctly display on the ticket.html
        """

        if filename == 'ticket.html':
            totalhours = [ field for field in data['fields'] if field['name'] == 'totalhours' ][0]
            ticket_id = data['ticket'].id
            if ticket_id is None: # new ticket
                field = '0'
            else:
                hours = '%.1f' % (self.get_total_hours(ticket_id) / 3600.0)
                field = tag.a(hours, href=req.href('hours', data['ticket'].id), 
                              title="hours for ticket %s" % data['ticket'].id)
            totalhours['rendered'] = field
            stream |= Transformer("//input[@id='field-totalhours']").replace(field)

        return stream


    ###### internal methods

    ### methods for date format

    def format_hours(self, seconds):
        """returns a formatted string of the number of hours"""
        precision = 1
        return str(round(seconds/3600., precision))

    def format_hours_and_minutes(self, seconds):
        """returns a formatted string of the number of hours"""
        return (seconds / 3600, (seconds % 3600) / 60)


    def format_date(self, date):
        return datetime.fromtimestamp(date).strftime(self.date_format)

    ### methods for the query interface

    def get_query(self, query_id):
        results = get_all_dict(self.env, "select title, description, query from ticket_time_query where id=%s", query_id)
        if not results:
            raise KeyError("No such query %s" % query_id)
        return results[0]


    def get_columns(self):
        return [ 'seconds_worked', 'worker', 'submitter', 
                 'time_started', 'time_submitted' ]

    def get_default_columns(self):
        return ['time_started', 'seconds_worked', 'worker',  ]


    def save_query(self, req):
        data = {}
        if req.method == "POST":
            assert req.perm.has_permission('TICKET_ADD_HOURS')
            id = int(req.args['id'])
            if id:
                #save over an existing query
                sql = """update ticket_time_query set title = %s, description = %s, query = %s where id = %s"""
                execute_non_query(self.env, sql, req.args['title'], 
                                  req.args['description'], req.args['query'],
                                  id)
            
            else:
                #create a new query
                sql = """insert into ticket_time_query(title, description,
                                                       query) 
                         values (%s, %s, %s)"""
                execute_non_query(self.env, sql, req.args['title'], 
                                  req.args['description'], req.args['query'])
                #fixme: duplicate title?
                id = get_scalar(self.env, "select id from ticket_time_query where title = %s", 0, req.args['title'])

            req.redirect(req.href('hours') + '?query_id=%s&%s' % (id, req.args['query']))

        action = req.args.get('action')
        if action == 'new':
            data['query'] = dict(id='0',
                                  description = '', 
                                  query=query_to_query_string(req.args))
        elif action == "edit":
            data['query'] = self.get_query(int(req.args['query_id']))
            data['query']['id'] = int(req.args['query_id'])

        else:
            #list
            data['queries'] = get_all_dict(self.env, "select id, title, description, query from ticket_time_query")
            return ('hours_listqueries.html', data, 'text/html')                    
        return ('hours_savequery.html', data, 'text/html')        

    def process_query(self, req):
        """redict to save, edit or delete a query based on arguments"""
        if req.args.get('save_query'):
            del req.args['save_query']
            if 'query_id' in req.args:
                del req.args['query_id']
            args = query_to_query_string(req.args)
            req.redirect(req.href(req.path_info) + "/query?action=new&" + args)
            return True
        elif req.args.get('edit_query'):
            del req.args['edit_query']
            args = query_to_query_string(req.args)
            req.redirect(req.href(req.path_info) + "/query?action=edit&" + args)
            return True
        elif req.args.get('delete_query'):
            assert req.perm.has_permission('TICKET_ADD_HOURS')
            query_id = req.args['query_id']
            sql = "delete from ticket_time_query where id=%s"
            execute_non_query(self.env, sql, query_id)
            if 'query_id' in req.args:
                del req.args['query_id']
            return False 

    def process_timeline(self, req):
        """/hours view"""

        if 'update' in req.args:
            # Reset session vars
            for var in ('query_constraints', 'query_time', 'query_tickets'):
                if var in req.session:
                    del req.session[var]

        if self.process_query(req):
            """the user has clicked on the 'Save Query' button; redirect them"""
            return

        ### lifted from trac.ticket.query.QueryModule.process_request
        
        req.perm.assert_permission('TICKET_VIEW')

        constraints = self._get_constraints(req)
        if not constraints and not 'order' in req.args:
            # If no constraints are given in the URL, use the default ones.
            if req.authname and req.authname != 'anonymous':
                qstring = 'status!=bogus'
                user = req.authname 
            else:
                email = req.session.get('email')
                name = req.session.get('name')
                qstring = 'status!=bogus'
                user = email or name or None 
                      
            if user: 
                qstring = qstring.replace('$USER', user) 
            self.log.debug('QueryModule: Using default query: %s', str(qstring)) 

            constraints = Query.from_string(self.env, qstring).constraints 
            # Ensure no field constraints that depend on $USER are used 
            # if we have no username.

            for constraint_set in constraints:
                for field, vals in constraint_set.items(): 
                    for val in vals: 
                        if val.endswith('$USER'): 
                            del constraint_set[field] 

        cols = req.args.get('col')
        if isinstance(cols, basestring):
            cols = [cols]

        if not cols:
            cols = ['id', 'summary'] + self.get_default_columns()

        # Since we don't show 'id' as an option to the user,
        # we need to re-insert it here.            
        if cols and 'id' not in cols: 
            cols.insert(0, 'id')

        rows = req.args.get('row', [])
        if isinstance(rows, basestring):
            rows = [rows]

        format = req.args.get('format')

        max = 0 # unlimited number of tickets

        # compute estimated hours even if not selected for columns
        rm_est_hours = False
        if not 'estimatedhours' in cols:
            cols.append('estimatedhours')
            rm_est_hours = True
        query = Query(self.env, req.args.get('report'),
                      constraints, cols, req.args.get('order'),
                      'desc' in req.args, req.args.get('group'),
                      'groupdesc' in req.args, 'verbose' in req.args,
                      rows,
                      req.args.get('page'), 
                      max)
        if rm_est_hours: # if not in the columns, remove estimatedhours
            cols.pop()                 

        return self.display_html(req, query)

    ### methods lifted from trac.ticket.query

    def _get_constraints(self, req):
        """PLEASE FILL IN THIS DOCSTRING!!!"""

        constraints = {} # PLEASE COMMENT WHAT THE HELL THIS VARIABLE MEANS

        ### PLEASE COMMENT WHAT IS DOING HERE AND WHY
        ticket_fields = [f['name'] for f in
                         TicketSystem(self.env).get_ticket_fields()]
        ticket_fields.append('id')

        # For clients without JavaScript, we remove constraints here if
        # requested
        remove_constraints = {}
        to_remove = [k[10:] for k in req.args.keys()
                     if k.startswith('rm_filter_')]
        if to_remove: # either empty or containing a single element
            match = re.match(r'(\w+?)_(\d+)$', to_remove[0])
            if match:
                remove_constraints[match.group(1)] = int(match.group(2))
            else:
                remove_constraints[to_remove[0]] = -1

        for field in [k for k in req.args.keys() if k in ticket_fields]:
            vals = req.args[field]
            if not isinstance(vals, (list, tuple)):
                vals = [vals]
            if vals:
                mode = req.args.get(field + '_mode')
                if mode:
                    vals = [mode + x for x in vals]
                if field in remove_constraints:
                    idx = remove_constraints[field]
                    if idx >= 0:
                        del vals[idx]
                        if not vals:
                            continue
                    else:
                        continue
                constraints[field] = vals

        return constraints

    def get_href(self, query, args, *a, **kw):
        base = query.get_href(*a, **kw)
        cols = args.get('col')
        if cols:
            if isinstance(cols, basestring):
                cols = [cols]
            base += '&' + "&".join("col=%s" % col for col in cols if not col in query.cols)

        now = datetime.now()
        if 'from_day' in args:
            base += '&from_year=%s&from_month=%s&from_day=%s&to_year=%s&to_month=%s&to_day=%s' % (
                args.get('from_year', now.year),
                args.get('from_month', now.month),
                args['from_day'],
                args.get('to_year', now.year),
                args.get('to_month', now.month),
                args.get('to_day', now.day),
                )
        return base.replace('/query', '/hours')
        

    def display_html(self, req, query):
        """returns the HTML according to a query for /hours view"""
        db = self.env.get_db_cnx()

        # The most recent query is stored in the user session;
        orig_list = None
        orig_time = datetime.now(utc)
        query_time = int(req.session.get('query_time', 0))
        query_time = datetime.fromtimestamp(query_time, utc)
        query_constraints = unicode(query.constraints)
        if query_constraints != req.session.get('query_constraints') \
                or query_time < orig_time - timedelta(hours=1):
            tickets = query.execute(req, db)
            # New or outdated query, (re-)initialize session vars
            req.session['query_constraints'] = query_constraints
            req.session['query_tickets'] = ' '.join([str(t['id']) for t in tickets])
        else:
            orig_list = [int(id) for id
                         in req.session.get('query_tickets', '').split()]
            tickets = query.execute(req, db, orig_list)
            orig_time = query_time

        context = Context.from_request(req, 'query')
        ticket_data = query.template_data(context, tickets, orig_list, orig_time, req)

        # For clients without JavaScript, we add a new constraint here if
        # requested
        constraints = ticket_data['clauses'][0]
        if 'add' in req.args:
            field = req.args.get('add_filter')
            if field:
                constraint = constraints.setdefault(field, {})
                constraint.setdefault('values', []).append('')
                # FIXME: '' not always correct (e.g. checkboxes)

        req.session['query_href'] = query.get_href(context.href)
        req.session['query_time'] = to_timestamp(orig_time)
        req.session['query_tickets'] = ' '.join([str(t['id'])
                                                 for t in tickets])

        # data dictionary for genshi
        data = {}

        # get data for saved queries
        query_id = req.args.get('query_id')
        if query_id:
            try:
                query_id = int(query_id)
            except ValueError:
                add_warning(req, "query_id should be an integer, you put '%s'" % query_id)
                query_id = None
        if query_id:
            data['query_id'] = query_id
            query_data = self.get_query(query_id)

            data['query_title'] = query_data['title']
            data['query_description'] = query_data['description']

        data.setdefault('report', None)
        data.setdefault('description', None)

        data['all_columns'] = query.get_all_columns() + self.get_columns()
        # Don't allow the user to remove the id column        
        data['all_columns'].remove('id')
        data['all_textareas'] = query.get_all_textareas()

        # need to re-get the cols because query will remove our fields
        cols = req.args.get('col')
        if isinstance(cols, basestring):
            cols = [cols]
        if not cols:
            cols = query.get_columns() + self.get_default_columns()
        data['col'] = cols

        now = datetime.now()
        # get the date range for the query
        if 'from_year' in req.args:
            from_date = get_date(req.args['from_year'], 
                                 req.args.get('from_month'),
                                 req.args.get('from_day'))

        else:
            from_date = datetime(now.year, now.month, now.day)
            from_date = from_date - timedelta(days=7) # 1 week ago, by default

        if 'to_year' in req.args:
            to_date = get_date(req.args['to_year'], 
                               req.args.get('to_month'),
                               req.args.get('to_day'),
                               end_of_day=True)
        else:
            to_date = now

        data['prev_week'] = from_date - timedelta(days=7)
        data['months'] = list(enumerate(calendar.month_name))
        data['years'] = range(now.year, now.year - 10, -1)
        data['days'] = range(1, 32)
        data['users'] = get_all_users(self.env)
        data['cur_worker_filter'] = req.args.get('worker_filter', '*any')

        data['from_date'] = from_date
        data['to_date'] = to_date

        ticket_ids = [t['id'] for t in tickets]

        # generate data for ticket_times
        time_records = self.get_ticket_hours(ticket_ids, from_date=from_date, to_date=to_date, worker_filter=data['cur_worker_filter'])

        data['query'] = ticket_data['query']
        data['context'] = ticket_data['context']
        data['row'] = ticket_data['row'] 
        if 'comments' in req.args.get('row', []):
            data['row'].append('comments')
        data['constraints'] = ticket_data['clauses']

        our_labels = dict([(f['name'], f['label']) for f in self.fields])
        labels = TicketSystem(self.env).get_ticket_field_labels()
        labels.update(our_labels)
        data['labels'] = labels

        order = req.args.get('order')
        desc = bool(req.args.get('desc'))
        data['order'] = order
        data['desc'] = desc

        headers = [{'name': col, 
                    'label' : labels.get(col),
                    'href': self.get_href(query, req.args,
                                          context.href, 
                                          order=col,
                                          desc=(col == order and not desc)
                                          )
                    } for col in cols]

        data['headers'] = headers

        data['fields'] = ticket_data['fields']
        data['modes'] = ticket_data['modes']


        # group time records
        time_records_by_ticket = {}
        for record in time_records:
            id = record['ticket']
            if id not in time_records_by_ticket:
                time_records_by_ticket[id] = []

            time_records_by_ticket[id].append(record)

        data['extra_group_fields'] = dict(ticket = dict(name='ticket', type='select', label='Ticket'),
                                          worker = dict(name='worker', type='select', label='Worker'))

        num_items = 0
        data['groups'] = []

        # merge ticket data into ticket_time records
        for key, tickets in ticket_data['groups']:
            ticket_times = []
            total_time = 0
            total_estimated_time = 0
            for ticket in tickets:
                records = time_records_by_ticket.get(ticket['id'], [])
                [rec.update(ticket) for rec in records]
                ticket_times += records

            # sort ticket_times, if needed
            if order in our_labels:                
                ticket_times.sort(key=lambda x: x[order], reverse=desc)
            data['groups'].append((key, ticket_times))
            num_items += len(ticket_times)


        data['double_count_warning'] = ''

        # group by ticket id or other time_ticket fields if necessary
        if req.args.get('group') in data['extra_group_fields']:
            query.group = req.args.get('group')
            if not query.group == "id":
                data['double_count_warning'] = "Warning: estimated hours may be counted more than once if a ticket appears in multiple groups"

            tickets = data['groups'][0][1]
            groups = {}
            for time_rec in tickets:
                key = time_rec[query.group]
                if not key in groups:
                    groups[key] = []
                groups[key].append(time_rec)
            data['groups'] = sorted(groups.items())

        total_times = dict((k, self.format_hours(sum(rec['seconds_worked'] for rec in v))) for k, v in data['groups'])
        total_estimated_times = {}
        for key, records in data['groups']:
            seen_tickets = set()
            est = 0
            for record in records:
                # do not double-count tickets
                id = record['ticket']
                if id in seen_tickets:
                    continue
                seen_tickets.add(id)
                estimatedhours = record.get('estimatedhours') or 0
                try:
                    estimatedhours = float(estimatedhours)
                except ValueError:
                    estimatedhours = 0
                est +=  estimatedhours * 3600
            total_estimated_times[key] = self.format_hours(est)

        data['total_times'] = total_times
        data['total_estimated_times'] = total_estimated_times

        # format records
        for record in time_records:
            if 'seconds_worked' in record:
                record['seconds_worked'] = self.format_hours(record['seconds_worked']) # XXX misleading name
            if 'time_started' in record:
                record['time_started'] = self.format_date(record['time_started'])
            if 'time_submitted' in record:
                record['time_submitted'] = self.format_date(record['time_submitted'])
            

        data['query'].num_items = num_items
        data['labels'] = TicketSystem(self.env).get_ticket_field_labels()
        data['labels'].update(labels)
        data['can_add_hours'] = req.perm.has_permission('TICKET_ADD_HOURS')

        data['multiproject'] = self.env.is_component_enabled(MultiprojectHours)

        from web_ui import TracUserHours
        data['user_hours'] = self.env.is_component_enabled(TracUserHours)

        # return the rss, if requested
        if req.args.get('format') == 'rss':
            return self.queryhours2rss(req, data)

        # return the csv, if requested
        if req.args.get('format') == 'csv':
            self.queryhours2csv(req, data)

        # add rss link
        rss_href = req.href(req.path_info, format='rss')
        add_link(req, 'alternate', rss_href, _('RSS Feed'),
                 'application/rss+xml', 'rss')

        # add csv link
        add_link(req, 'alternate', req.href(req.path_info, format='csv', **req.args), 'CSV', 'text/csv', 'csv')
                
        # add navigation of weeks
        prev_args = dict(req.args)        
        next_args = dict(req.args)
                
        prev_args['from_year'] = (from_date - timedelta(days=7)).year
        prev_args['from_month'] = (from_date - timedelta(days=7)).month
        prev_args['from_day'] = (from_date - timedelta(days=7)).day
        prev_args['to_year'] = from_date.year
        prev_args['to_month'] = from_date.month
        prev_args['to_day'] = from_date.day        
        
        next_args['from_year'] = to_date.year
        next_args['from_month'] = to_date.month
        next_args['from_day'] = to_date.day
        next_args['to_year'] = (to_date + timedelta(days=7)).year
        next_args['to_month'] = (to_date + timedelta(days=7)).month
        next_args['to_day'] = (to_date + timedelta(days=7)).day
        
        add_link(req, 'prev', self.get_href(query, prev_args, context.href), _('Prev Week'))
        add_link(req, 'next', self.get_href(query, next_args, context.href), _('Next Week'))                                            
        prevnext_nav(req, _('Prev Week'), _('Next Week'))
        
        add_ctxtnav(req, 'Cross-Project Hours', req.href.hours('multiproject'))
        add_ctxtnav(req, 'Hours by User', req.href.hours('user', from_day=from_date.day, 
                                                                 from_month=from_date.month, 
                                                                 from_year=from_date.year, 
                                                                 to_day=to_date.year, 
                                                                 to_month=to_date.month, 
                                                                 to_year=to_date.year))
        add_ctxtnav(req, 'Saved Queries', req.href.hours('query/list'))
        
        add_stylesheet(req, 'common/css/report.css')
        add_script(req, 'common/js/query.js')
        
        return ('hours_timeline.html', data, 'text/html')
                          
    def process_ticket(self, req):
        """process a request to /hours/<ticket number>"""

        # get the ticket
        path = req.path_info.rstrip('/')
        ticket_id = int(path.split('/')[-1]) # matches a ticket number
        ticket = Ticket(self.env, ticket_id)

        if req.method == 'POST':
            if 'addhours' in req.args:
                return self.do_ticket_change(req, ticket)
            if 'edithours' in req.args:
                return self.edit_ticket_hours(req, ticket)

        # XXX abstract date stuff as this is used multiple places
        now = datetime.now()
        months = [ (i, calendar.month_name[i], i == now.month) for i in range(1,13) ]
        years = range(now.year, now.year - 10, -1)
        days = [ (i, i == now.day) for i in range(1, 32) ]

        time_records = self.get_ticket_hours(ticket.id)
        time_records.sort(key=lambda x: x['time_started'], reverse=True)

        # add additional data for the template
        total = 0
        for record in time_records:
            record['date_started'] = self.format_date(record['time_started'])
            record['hours_worked'], record['minutes_worked'] = self.format_hours_and_minutes(record['seconds_worked'])
            total += record['seconds_worked']
        total = self.format_hours(total)

        data = {
            'can_add_hours': req.perm.has_permission('TICKET_ADD_HOURS'),
            'can_add_others_hours': req.perm.has_permission('TRAC_ADMIN'),
            'days': days,
            'months': months,
            'years': years,
            'users': get_all_users(self.env),
            'total': total,
            'ticket': ticket,
            'time_records': time_records
        }
        
        # return the rss, if requested
        if req.args.get('format') == 'rss':
            return self.tickethours2rss(req, data)

        # add rss link
        rss_href = req.href(req.path_info, format='rss')
        add_link(req, 'alternate', rss_href, _('RSS Feed'),
                 'application/rss+xml', 'rss')        
        add_ctxtnav(req, 'Back to Ticket #%s' %ticket_id, req.href.ticket(ticket_id))        

        return ('hours_ticket.html', data, 'text/html')


    ### methods for transforming data to rss

    def queryhours2rss(self, req, data):
        """adapt data for /hours to RSS"""
        adapted = {}
        adapted['title'] = 'Hours worked on %s from %s to %s' % (self.env.project_name, 
                                                                 data['from_date'].strftime(self.date_format),
                                                                 data['to_date'].strftime(self.date_format))
        adapted['description'] = data['description'] or adapted['title']
        adapted['url'] = req.abs_href(req.path_info)
        items = []
        for group in data['groups']:
            for entry in group[1]:
                item = {}
                hours = float(entry['seconds_worked']) 
                minutes = int(60*(hours-int(hours)))
                hours = int(hours)
                title = '%s:%02d hours worked by %s' % (hours, minutes, 
                                                        entry['worker'])
                item['title'] = title
                item['description'] = title                
                comments = entry.get('comments')
                if comments:                    
                    item['description'] += ': %s' % comments

                # the 'GMT' business is wrong
                # maybe use py2rssgen a la bitsyblog?
                time_started = dateutil.parser.parse(entry['time_started']) # XXX hack
                item['date'] = time_started.strftime('%a, %d %b %Y %T GMT')
                
                link = req.abs_href(req.path_info, entry['ticket'])
                item['guid'] = '%s#%s' % (link, entry['id'])
                item['url'] = item['guid']
                item['comments'] = req.abs_href('ticket', entry['ticket'])
                items.append(item)
            
        adapted['items'] = items
        return ('hours.rss', adapted, 'application/rss+xml')



    def tickethours2rss(self, req, data):
        """adapt data for /hours/<ticket number> to RSS"""
        adapted = {}
        adapted['title'] = 'Hours worked for ticket %s' % data['ticket']

        # could put more information in the description
        adapted['description'] = data['ticket']['summary']

        link = req.abs_href(req.path_info)
        adapted['url'] = link
        items = []
        for record in data['time_records']:
            item = {}
            title = '%s:%02d hours worked by %s' % (record['hours_worked'], 
                                                   record['minutes_worked'],
                                                   record['worker'])
            item['title'] = title
            item['description'] = '%s%s' % (title, (': %s' % record['comments']) or '')

            # the 'GMT' business is wrong
            # maybe use py2rssgen a la bitsyblog?
            item['date'] = datetime.fromtimestamp(float('%s' % record['time_started'])).strftime('%a, %d %b %Y %T GMT')

            # could add these links to the template
            item['guid'] = '%s#%s' % (link, record['id'])
            item['url'] = item['guid']
            item['comments'] = req.abs_href('ticket', data['ticket'])

            items.append(item)
        adapted['items'] = items
        return ('hours.rss', adapted, 'text/xml')


    ### method for transforming hours to csv
    def queryhours2csv(self, req, data):
        buffer = StringIO()
        writer = csv.writer(buffer)

        if data['cur_worker_filter'] != '*any':
            title = 'Hours for %s' % data['cur_worker_filter']
        else:
            title = 'Hours'
        writer.writerow([title, req.abs_href()])

        constraint = data['constraints'][0]
        for key in constraint:
            if key == 'status' and constraint[key]['values'] == ['bogus']:
                continue  # XXX I actually have no idea why this is here
            writer.writerow([key] + constraint[key]['values'])
        writer.writerow([])

        format = '%B %d, %Y'
        writer.writerow(['From', 'To'])
        writer.writerow([data[i].strftime(format) 
                         for i in 'from_date', 'to_date'])
        writer.writerow([])

        for groupname, results in data['groups']:
            if groupname:
                writer.writerow(unicode(groupname))
            writer.writerow([unicode(header['label'])
                             for header in data['headers']])
            for result in results:
                row = []
                for header in data['headers']:
                    value = result[header['name']]
                    row.append(unicode(value).encode('utf-8'))
                writer.writerow(row)
            writer.writerow([])

        req.send(buffer.getvalue(), "text/csv")


    ### methods for adding and editting hours associated with tickets

    def do_ticket_change(self, req, ticket):
        """respond to a request to add hours to a ticket"""

        # permission check
        req.perm.require('TICKET_ADD_HOURS')

        # 
        now = datetime.now()
        logged_in_user = req.authname
        worker = req.args.get('worker', logged_in_user)
        if not worker == logged_in_user:
            assert req.perm.has_permission('TICKET_ADMIN')

        # when the work was done
        if 'year' in req.args: # assume month and day are provided

            started = datetime(*map(int, [req.args[i] for i in 'year', 'month', 'day']))
            if started == datetime(now.year, now.month, now.day):
                # assumes entries made for today should be ordered
                # as they are entered
                started = now

        else:
            started = now

        # how much work was done
        hours = req.args['hours'].strip() or 0
        minutes = req.args['minutes'].strip() or 0
        try:
            seconds_worked = int(float(hours) * 3600 + float(minutes) * 60)
        except ValueError:
            # XXX handle better
            raise ValueError("Please enter a valid number of hours")
            req.redirect(req.href(req.path_info))
        
        # comments on hours event
        comments = req.args.get('comments', '').strip()

        # add the hours
        self.add_ticket_hours(ticket.id, worker, seconds_worked, 
                              submitter=logged_in_user, time_started=started, 
                              comments=comments)

        # if comments are made, anote the ticket
        if comments:
            comment = "[%s %s\thours] logged for %s: ''%s''" % ('/hours/%s' % ticket.id,
                                                           self.format_hours(seconds_worked),
                                                           worker,
                                                           comments)

            # avoid adding hours that are (erroneously) noted in the comments
            # see #4791
            comment = comment.replace(' ', '\t') 

            ticket.save_changes(logged_in_user, comment)
#            index = len(ticket.get_changelog()) - 1 # XXX can/should this be used?

        location = req.environ.get('HTTP_REFERER', req.href(req.path_info))
        req.redirect(location)


    def edit_ticket_hours(self, req, ticket):
        """respond to a request to edithours for a ticket"""

        # permission check
        req.perm.require('TICKET_ADD_HOURS')

        # set hours
        new_hours = {}
        for field, newval in req.args.items():
            if field.startswith("hours_"):
                id = int(field[len("hours_"):])
                new_hours[id] = (int(float(newval) * 3600) + 
                                 int(float(req.args['minutes_%s' % id]) * 60))

        # remove checked hours
        for field, newval in req.args.items():
            if field.startswith("rm_"):
                id = int(field[len("rm_"):])
                new_hours[id] = 0

        hours = self.get_ticket_hours(ticket.id)
        tickets = set()

        # check permission if you're editing another's hours
        for hour in hours:
            tickets.add(hour['ticket'])

            id = hour['id']
            if not id in new_hours:
                continue

            if not hour['worker'] == req.authname:
                req.perm.require("TRAC_ADMIN")


        # perform the edits
        for hour in hours:
            tickets.add(hour['ticket'])

            id = hour['id']
            if not id in new_hours:
                continue

            if new_hours[id]:
                execute_non_query(self.env, "update ticket_time set seconds_worked=%s where id=%s", new_hours[id], id)
            else:
                execute_non_query(self.env, "delete from ticket_time where id=%s", id)

        self.update_ticket_hours(tickets)

        req.redirect(req.href(req.path_info))

