# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 John Hampton <pacopablo@pacopablo.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: John Hampton <pacopablo@pacopablo.com>
# 
# Concept code for template filter created by Noah Kantrowitz on
# 2008-02-19.

import re
import copy

from genshi.filters.transform import Transformer
from genshi.builder import tag

from trac.core import *
from trac.web.api import IRequestHandler, ITemplateStreamFilter
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.ticket.query import Query, QueryModule
from trac.ticket.api import TicketSystem, ITicketManipulator
from trac.ticket.model import Ticket
from trac.ticket.notification import TicketNotifyEmail
from trac.mimeview.api import Context
from trac.web.chrome import add_ctxtnav, add_link, add_script, add_stylesheet, \
                            add_warning, INavigationContributor, Chrome
from trac.config import ListOption, Option
from trac.util import get_reporter_id

from pprint import PrettyPrinter
from pkg_resources import resource_filename

__all__ = ['TasklistPlugin']

def _pprint(object, prefix=""):
    """ Pretty Print the given object with an optional prefix.  Used for debugging"""
    if prefix:
        print prefix
    PrettyPrinter().pprint(object)
    pass


class TasklistPlugin(QueryModule):
    implements(ITemplateProvider, ITemplateStreamFilter)

    ticket_manipulators = ExtensionPoint(ITicketManipulator)

    field_name = Option('tasklist', 'tasklist_field', default='action_item')

    default_query = Option('tasklist', 'default_query', 
                            default='status!=closed&owner=$USER',
                            doc='The default tasklist query for authenticated users.')
   
    default_anonymous_query = Option('tasklist', 'default_anonymous_query', 
                               default='status!=closed&cc~=$USER',
                               doc='The default tasklist query for anonymous users.')
    
    default_cols = ListOption('tasklist', 'default_cols', 
                              default=['id', 'summary', 'priority'],
                              doc='The default list of columns to show in the tasklist.')

    # INavigationContributor methods    
    def get_active_navigation_item(self, req):
        return 'tasklist'

    def get_navigation_items(self, req):
        if req.perm.has_permission('TICKET_VIEW'):
            yield ('mainnav', 'tasklist',
                   tag.a('Tasklist', href=req.href.tasklist()))

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/tasklist')

    def process_request(self, req):
        req.perm.assert_permission('TICKET_VIEW')
        
        if not self.env.config.has_option('ticket-custom', self.field_name):
            raise TracError('Configuration error: the custom ticket field "%s" has not been defined '
                            'in the [ticket-custom] section of trac.ini. See the documentation ' 
                            'for more info on configuring the TaskListPlugin.'  % self.field_name)
        
        constraints = self._get_constraints(req)
        if not constraints and not 'order' in req.args:
            # If no constraints are given in the URL, use the default ones.
            if req.authname and req.authname != 'anonymous':
                qstring = self.default_query
                user = req.authname
            else:
                email = req.session.get('email')
                name = req.session.get('name')
                qstring = self.default_anonymous_query
                user = email or name or None
                     
            if user:
                qstring = qstring.replace('$USER', user)
            self.log.debug('TasklistPlugin: Using default query: %s', qstring)
            constraints = Query.from_string(self.env, qstring).constraints
            # Ensure no field constraints that depend on $USER are used
            # if we have no username.
            for field, vals in constraints.items():
                for val in vals:
                    if val.endswith('$USER'):
                        del constraints[field]

        cols = req.args.get('col')
        if not cols:
            cols = self.default_cols
            cols.append(self.field_name)
            
        if isinstance(cols, basestring):
            cols = [cols]
        form_cols = copy.copy(cols)
        # Since we don't show 'id' or the tasklist_field as an option
        # to the user, we need to re-insert it here.           
        if cols and 'id' not in cols:
            cols.insert(0, 'id')
        if cols and self.field_name not in cols:
            cols.insert(0, self.field_name)

        rows = req.args.get('row', [])
        if isinstance(rows, basestring):
            rows = [rows]
        
        q = Query(self.env, constraints=constraints, cols=cols)  
        query = Query(self.env, req.args.get('report'),
                      constraints, cols, req.args.get('order'),
                      'desc' in req.args, req.args.get('group'),
                      'groupdesc' in req.args, 'verbose' in req.args,
                      rows,
                      req.args.get('limit'))

        if 'update' in req.args:
            # Reset session vars
            for var in ('query_constraints', 'query_time', 'query_tickets'):
                if var in req.session:
                    del req.session[var]
            req.redirect(q.get_href(req.href).replace('/query', '/tasklist'))

        if 'add' in req.args:
            req.perm.require('TICKET_CREATE')
            t = Ticket(self.env)
            if req.method == 'POST' and 'field_owner' in req.args and \
                   'TICKET_MODIFY' not in req.perm:
                del req.args['field_owner']
            self._populate(req, t)
            reporter_id = req.args.get('field_reporter') or \
                          get_reporter_id(req, 'author')
            t.values['reporter'] = reporter_id
            valid = None
            valid = self._validate_ticket(req, t)
            if valid:
                t.insert()
                # Notify
                try:
                    tn = TicketNotifyEmail(self.env)
                    tn.notify(t, newticket=True)
                except Exception, e:
                    self.log.exception("Failure sending notification on creation of "
                                       "ticket #%s: %s" % (t.id, e))
            req.redirect(q.get_href(req.href).replace('/query', '/tasklist'))


        template, data, mime_type = self.display_html(req, query)

        # We overlap the query session href var so that if a ticket is
        # entered from the tasklist the "Back to Query" link will
        # come back to the tasklist instead of the query module.
        query_href = req.session['query_href']
        req.session['query_href'] = query_href.replace('/query', '/tasklist')

        data['title'] = 'Task List'
        data['all_columns'].remove(self.field_name)
        #_pprint(data['tickets'])
        for ticket in data['tickets']:
            summary = ticket['summary']
            action = ticket[self.field_name]
            ticket['title'] = summary
            ticket['summary'] = action !=  '--' and action or summary
            continue
        for i, header in enumerate(data['headers']):
            header['href'] = header['href'].replace('/query', '/tasklist')
            if header['name'] == self.field_name:
                del_index = i
            continue
        del data['headers'][del_index]
        data['ticket_fields'] = self._get_ticket_fields(data)

        add_stylesheet(req, 'tasklist/css/tasklist.css')
        return 'tasklist.html', data, mime_type

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        """ Hack up the query inteface to do what we want. """
        if filename == 'tasklist.html':
            for ticket in data['tickets']:
                title = ticket['title']
                stream |= Transformer('//td[@class="summary"]/a[@href="%s"]' % ticket['href']
                                     ).attr('title', title)
                                         
        return stream

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('tasklist', resource_filename(__name__, 'htdocs'))]

    # Internal methods
    def _get_ticket_fields(self, data):
        """ Return a list of the ticket fields corresponding to the output columns

        The data returned is used for ticket field input
        """
        ts = TicketSystem(self.env)
        fields = ts.get_ticket_fields()
        results = []
        for header in data['headers'][1:]:
            for field in fields:
                if field['name'] == header['name']:
                    results.append(field)
                continue
            continue
        return results
            

    def _populate(self, req, ticket):
        fields = dict([(k[6:],v) for k,v in req.args.iteritems()
                      if k.startswith('field_')])
        if not fields.has_key('status'):
            fields['status'] = 'new'

        if not fields.has_key('owner') and \
           req.perm.has_permission('TICKET_MODIFY'):
            fields['owner'] = req.authname
        ticket.populate(fields)
                              

        # special case for updating the Cc: field
        if 'cc_update' in req.args:
            cc_action, cc_entry, cc_list = self._toggle_cc(req, ticket['cc'])
            if cc_action == 'remove':
                cc_list.remove(cc_entry)
            elif cc_action == 'add':
                cc_list.append(cc_entry)
            ticket['cc'] = ', '.join(cc_list)
        pass


    def _validate_ticket(self, req, ticket):
        valid = True

        # Mid air collision?
        if ticket.exists and (ticket._old or comment):
            if req.args.get('ts') != str(ticket.time_changed):
                add_warning(req, _("Sorry, can not save your changes. "
                              "This ticket has been modified by someone else "
                              "since you started"))
                valid = False

        # Always validate for known values
        for field in ticket.fields:
            if 'options' not in field:
                continue
            if field['name'] == 'status':
                continue
            name = field['name']
            if name in ticket.values and name in ticket._old:
                value = ticket[name]
                if value:
                    if value not in field['options']:
                        add_warning(req, '"%s" is not a valid value for '
                                    'the %s field.' % (value, name))
                        valid = False
                elif not field.get('optional', False):
                    add_warning(req, 'field %s must be set' % name)
                    valid = False

        # Validate description length
        max_description_size = int(self.config.get('ticket', 'max_description_size', 262144))
        if len(ticket['description'] or '') > max_description_size:
            add_warning(req, _('Ticket description is too long (must be less '
                          'than %(num)s characters)',
                          num=max_description_size))
            valid = False

        # Custom validation rules
        for manipulator in self.ticket_manipulators:
            for field, message in manipulator.validate_ticket(req, ticket):
                valid = False
                if field:
                    add_warning(req, _("The ticket field '%(field)s' is "
                                  "invalid: %(message)s",
                                  field=field, message=message))
                else:
                    add_warning(req, message)
        return valid


#    def process_request(self, req):

#        # Add registered converters
#        for conversion in Mimeview(self.env).get_supported_conversions(
#                                             'trac.ticket.Query'):
#            add_link(req, 'alternate',
#                     query.get_href(req.href, format=conversion[0]),
#                     conversion[1], conversion[4], conversion[0])
#
#        format = req.args.get('format')
#        if format:
#            Mimeview(self.env).send_converted(req, 'trac.ticket.Query', query,
#                                              format, 'query')
#
#        return self.display_html(req, query)

