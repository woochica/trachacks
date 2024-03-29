# -*- coding: utf-8 -*-
# Copyright (C) 2006 Ashwin Phatak
# Copyright (C) 2007 Dave Gynn
# Copyright (C) 2010 Brian Meeker

from trac.core import *
from trac.config import Option, ListOption
from trac.db.api import with_transaction
from trac.perm import IPermissionRequestor
from trac.ticket import TicketSystem, Ticket
from trac.ticket.notification import TicketNotifyEmail
from trac.web import IRequestHandler
from trac.web.chrome import Chrome, \
                            add_script, add_stylesheet
from trac.util.datefmt import to_datetime, to_utimestamp, utc
from datetime import datetime
import re

__all__ = ['BatchModifyModule']

class BatchModifyModule(Component):
    
    implements(IRequestHandler, IPermissionRequestor)
    
    fields_as_list = ListOption("batchmod", "fields_as_list", 
                default="keywords", 
                doc="field names modified as a value list(separated by ',')")
    list_separator_regex = Option("batchmod", "list_separator_regex",
                default='[,\s]+',
                doc="separator regex used for 'list' fields")
    list_connector_string = Option("batchmod", "list_connector_string",
                default=' ',
                doc="Connector string for 'list' fields. Defaults to a space.")

    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'TICKET_BATCH_MODIFY'
        
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/batchmodify'

    def process_request(self, req):        
        if req.method=='POST' and self._has_permission(req):
            self.log.debug('BatchModifyModule: executing batchmod')
            
            batch_modifier = BatchModifier(self.fields_as_list, 
                                           self.list_separator_regex, 
                                           self.list_connector_string)
            batch_modifier.process_request(req, self.env, self.log)
            
            req.redirect(req.args.get('query_href'))
        else:
            self.log.debug('BatchModifyModule: rendering form')
            

    def _generate_form(self, req, data):
        batchFormData = dict(data)
        batchFormData['query_href']= req.session['query_href'] \
                                     or req.href.query()
        batchFormData['notify_enabled'] = self.config.getbool('notification', 
                                                        'smtp_enabled', False)
        
        ticketSystem = TicketSystem(self.env)
        fields = []
        for field in ticketSystem.get_ticket_fields():
            if field['name'] not in ('summary', 'reporter', 'description'):
                fields.append(field)
            if field['name'] == 'owner' \
                and hasattr(ticketSystem, 'eventually_restrict_owner'):
                ticketSystem.eventually_restrict_owner(field)
        fields.sort(key=lambda f: f['name'])
        batchFormData['fields']=fields

        add_script(req, 'batchmod/js/batchmod.js')
        add_stylesheet(req, 'batchmod/css/batchmod.css')
        stream = Chrome(self.env).render_template(req, 'batchmod.html',
              batchFormData, fragment=True)
        return stream.select('//form[@id="batchmod_form"]')

    def _has_permission(self, req):
        return req.perm.has_permission('TICKET_ADMIN') or \
                req.perm.has_permission('TICKET_BATCH_MODIFY')

class BatchModifier:
    """Modifies a batch of tickets"""
    
    def __init__(self, fields_as_list, list_separator_regex, 
                 list_connector_string):
        """Pull all the config values in."""
        self._fields_as_list = fields_as_list
        self._list_separator_regex = list_separator_regex
        self._list_connector_string = list_connector_string
    
        # Internal methods 
    def process_request(self, req, env, log):
        tickets = req.session['query_tickets'].split(' ')
        comment = req.args.get('batchmod_value_comment', '')
        modify_changetime = bool(req.args.get(
                                              'batchmod_modify_changetime',
                                              False))
        send_notifications = bool(req.args.get(
                                              'batchmod_send_notifications',
                                              False))
        
        values = self._get_new_ticket_values(req, env) 
        self._check_for_resolution(values)
        self._remove_resolution_if_not_closed(values)

        selectedTickets = req.args.get('selectedTickets')
        log.debug('BatchModifyPlugin: selected tickets: %s', selectedTickets)
        selectedTickets = isinstance(selectedTickets, list) \
                          and selectedTickets or selectedTickets.split(',')
        if not selectedTickets:
            raise TracError, 'No tickets selected'
        
        self._save_ticket_changes(req, env, log, selectedTickets, tickets, 
                                  values, comment, modify_changetime, send_notifications)

    def _get_new_ticket_values(self, req, env):
        """Pull all of the new values out of the post data."""
        values = {}
        
        # Get the current users name.
        if req.authname and req.authname != 'anonymous':
            user = req.authname
        else:
            user = req.session.get('email') or req.session.get('name') or None
        
        for field in TicketSystem(env).get_ticket_fields():
            name = field['name']
            if name not in ('summary', 'reporter', 'description'):
                value = req.args.get('batchmod_value_' + name)
                if name == 'owner' and value == '$USER':
                    value = user
                if value is not None:
                    values[name] = value
        return values
    
    def _check_for_resolution(self, values):
        """If a resolution has been set the status is automatically
        set to closed."""
        if values.has_key('resolution'):
            values['status'] = 'closed'
    
    def _remove_resolution_if_not_closed(self, values):
        """If the status is set to something other than closed the
        resolution should be removed."""
        if values.has_key('status') and values['status'] is not 'closed':
            values['resolution'] = ''
  
    def _save_ticket_changes(self, req, env, log, selectedTickets, tickets,
                             new_values, comment, modify_changetime, send_notifications):
        @with_transaction(env)
        def _implementation(db):
            for id in selectedTickets:
                if id in tickets:
                    t = Ticket(env, int(id))
                    new_changetime = datetime.now(utc)
                    
                    log_msg = ""
                    if not modify_changetime:
                        original_changetime = to_utimestamp(t.time_changed)
                    
                    _values = new_values.copy()
                    for field in [f for f in new_values.keys() \
                                  if f in self._fields_as_list]:
                        _values[field] = self._merge_keywords(t.values[field],
                                                              new_values[field],
                                                              log)
                    
                    t.populate(_values)
                    t.save_changes(req.authname, comment, when=new_changetime)

                    if send_notifications:
                        tn = TicketNotifyEmail(env)
                        tn.notify(t, newticket=0, modtime=new_changetime)

                    if not modify_changetime:
                        self._reset_changetime(env, original_changetime, t)
                        log_msg = "(changetime not modified)"

                    log.debug('BatchModifyPlugin: saved changes to #%s %s' % 
                              (id, log_msg))

    def _merge_keywords(self, original_keywords, new_keywords, log):
        """
        Prevent duplicate keywords by merging the two lists.
        Any keywords prefixed with '-' will be removed.
        """
        log.debug('BatchModifyPlugin: existing keywords are %s', 
                  original_keywords)
        log.debug('BatchModifyPlugin: new keywords are %s', new_keywords)
        
        regexp = re.compile(self._list_separator_regex)
        
        new_keywords = [k.strip() for k in regexp.split(new_keywords) if k]
        combined_keywords = [k.strip() for k 
                             in regexp.split(original_keywords) if k]
        
        for keyword in new_keywords:
            if keyword.startswith('-'):
                keyword = keyword[1:]
                while keyword in combined_keywords:
                    combined_keywords.remove(keyword)
            else:
                if keyword not in combined_keywords:
                    combined_keywords.append(keyword)
        
        log.debug('BatchModifyPlugin: combined keywords are %s', 
                  combined_keywords)
        return self._list_connector_string.join(combined_keywords)
    
    def _reset_changetime(self, env, original_changetime, ticket):
        db = env.get_db_cnx()
        db.cursor().execute("UPDATE ticket set changetime=%s where id=%s" 
                            % (original_changetime, ticket.id))
        db.commit()
