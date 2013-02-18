# -*- coding: utf-8 -*-
# Copyright (C) 2012 Zack Shahan
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import Component, implements
from trac.ticket.api import ITicketChangeListener, ITicketManipulator
from trac.resource import ResourceNotFound
from tracrpc import *
from trac.web.href import Href
from urlparse import urlsplit
import xmlrpclib
import re

class RemoteTicketConditionalCreate(Component):
    implements(ITicketChangeListener,
               ITicketManipulator)

    def __init__(self):
        self.EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
        self.sep = re.compile(r'[\s,]+')
        self.defin_patt = re.compile(r'(\w+)\.(\w+)')
        self._rtccs = self._get_rtccs_config()
        self._intertracs = self._get_remotes_config()
        
    # create xmlrpc connection to remote intertrac    
    def _xmlrpc_connect(self, rintertrac):
        remote_trac = self._get_remote_trac(rintertrac)['url']
        addr_split = urlsplit(remote_trac)
        if self.rtcc['xmlrpc_user']:
            final_url = ''.join((addr_split.scheme, '://', self.rtcc['xmlrpc_user'],
                                 ':', self.rtcc['xmlrpc_password'], '@',
                                 addr_split.netloc, addr_split.path, '/login'))
        else:
            final_url = remote_trac
            
        xmlrpc_addr = Href(final_url).rpc()
        server = xmlrpclib.ServerProxy(xmlrpc_addr)
        
        return server
    
    # converts users in ticket to email addresses for remote intertrac
    def _get_email_addrs(self, user):
        addr_list = []
        with self.env.db_query as db:
            cursor = db.cursor()
            for email in self.sep.split(user):
                if not self.EMAIL_REGEX.match(email):
                    cursor.execute('''select value from session_attribute
                                    where name = "email" and sid = %s''', (email,))
                result = ','.join(rec[0] for rec in cursor.fetchall())
                if not result:
                    result = email
                else:
                    result = email
        addr_list.append(result)
        final_addr_list = ','.join(addr_list)
        return final_addr_list


    # create the ticket on the specified intertrac
    def _create_remote_ticket(self, rintertrac, ticket, author, comment):
        server = self._xmlrpc_connect(rintertrac)
        tsummary = str(ticket.values['summary'])
        if comment:
            message = ''.join(('\n\nLatest comment from ', self._rtccs['intertrac_name'],
                                ':#', str(ticket.id), ' :\n\n Author: \'\'', author,
                                '\'\'\n Comment: \'\'', comment, '\'\''))
        else:
            message = '' 
        tdescription = str(ticket.values['description'] + message)
        attrs = {
                'status': 'new',
                'type': self.rtcc['type'],
                'component': self.rtcc['component'],
                'reporter' : '%s' % (self._get_email_addrs(ticket.values['reporter'])),
                'cc' : '%s,%s' % (self._get_email_addrs(ticket.values['owner']),
                                  self._get_email_addrs(ticket.values['cc'])),
                 self.rtcc['remote_cfield'] : '%s:#%s' % (self._rtccs['intertrac_name'],
                                                         ticket.id)
            }
        if self.rtcc['copy_fields'] and self.rtcc['copy_fields'] != '':
            fields = self.rtcc['copy_fields']
            for c in (x.strip() for x in fields.split(',')):
                if c in ticket.values and ticket.values[str(c)] != '':
                    if c not in self.rtcc.keys():
                        attrs[str(c)] = ticket.values[str(c)]
        
        rticket = server.ticket.create(tsummary, tdescription, attrs)
        return rticket
    
        # update the ticket on the specified intertrac
    def _update_remote_ticket(self, rintertrac, rticket, ticket, author):
        server = self._xmlrpc_connect(rintertrac)
        comment = 'Ticket %s:#%s has been closed' % (self._rtccs['intertrac_name'],
                                                    ticket.id)
        attrs = server.ticket.get(int(rticket))
        for x in attrs:
            if isinstance(x, dict):
                if 'status' in x:
                    if x['status'] != 'closed':
                        server.ticket.update(int(rticket), comment, {}, False, author)
                        
    
    # main routine. if status falls into this scope, create the remote ticket and
    # add the remote ticket link to the current ticket
    def ticket_changed(self, ticket, comment, author, old_values):
        if 'status' in ticket.values:
            new_status = ticket.values['status']
            
            if new_status in self._rtccs.keys():
                self.rtcc = self._get_rtcc(new_status)
                if 'status' in old_values \
                and old_values['status'] != self._rtccs[new_status]:
                    rticket = self._create_remote_ticket(self.rtcc['remote_intertrac'],
                                                         ticket, author, comment)
                    self._update_intertrac_link(rticket,
                                                self.rtcc['remote_intertrac'],
                                                ticket)
                
            if new_status == 'closed':
                with self.env.db_query as db:
                    cursor = db.cursor()
                    cursor.execute('''select name, value from ticket_custom 
                                    where ticket = %s''', (ticket.id,))
                    result = cursor.fetchall()
                for x in self._rtccs.keys():
                    self.rtcc = self._get_rtcc(x)
                    if isinstance(self.rtcc, dict):
                        if 'update_on_close' in self.rtcc.keys() \
                        and self.rtcc['update_on_close'] != '' \
                        and str(self.rtcc['update_on_close']).lower() == 'true':
                            for k, v in result:
                                if self.rtcc['local_cfield'] == k and v != '':
                                    rticket = v.split(':#')
                                    self._update_remote_ticket(rticket[0],
                                                               rticket[1],
                                                               ticket,
                                                               author)

    def ticket_created(self, ticket):
        pass 
    
    def ticket_deleted(self, ticket):
        pass
    
    def validate_ticket(self, req, ticket):
        # Make sure custom field is empty before we add the link
        if 'status' in ticket.values and ticket.values['status'] in self._rtccs.keys():
            if ticket.values[str(self._get_rtcc(ticket.values['status'])['local_cfield'])]:
                return [(None, "Cannot update ticket that has already been %s." % 
                        (ticket.values['status']))]
        return []

    # add the intertrac link to the ticket
    def _update_intertrac_link(self, rticket, rintertrac, ticket):
        intertrac_link = '%s:#%s' % (rintertrac, rticket)
        with self.env.db_transaction as db:
            cursor = db.cursor()
            cursor.execute('replace into ticket_custom values (%s,%s,%s)',
                           (ticket.id,
                            self.rtcc['local_cfield'],
                            intertrac_link))

    def _get_remote_tracs(self):
        intertracs = [v for k, v in self._intertracs.items() 
                      if isinstance(v, dict) and 'url' in v]
        intertracs.sort()
        return intertracs
        
    def _get_remote_trac(self, rintertrac):
        try:
            intertrac = self._intertracs[rintertrac]
        except KeyError:
            raise ResourceNotFound("Remote Trac '%s' is unknown." 
                                   % rintertrac,
                                   "Invalid InterTrac alias")
        try:
            intertrac['url']
        except KeyError:
            raise ResourceNotFound("Remote Trac '%s' has no address configured."
                                   % rintertrac,
                                   "Invalid InterTrac alias")
        return intertrac
    
    def _get_rtcc(self, status):
        try:
            rtcc = self._rtccs[status]
        except KeyError:
            raise ResourceNotFound("status '%s' is unknown." 
                                   % status)
        if not isinstance(rtcc, unicode):
            try:
                rtcc['component']
            except KeyError:
                raise ResourceNotFound("%s.component is unknown."
                                       % status)
            try:
                rtcc['local_cfield']
            except KeyError:
                raise ResourceNotFound("%s.local_cfield is unknown."
                                       % status)
            try:
                rtcc['remote_cfield']
            except KeyError:
                raise ResourceNotFound("%s.remote_cfield is unknown."
                                       % status)
            try:
                rtcc['remote_intertrac']
            except KeyError:
                raise ResourceNotFound("%s.remote_intertrac is unknown."
                                       % status)
            try:
                rtcc['type']
            except KeyError:
                raise ResourceNotFound("%s.type is unknown."
                                       % status)
            return rtcc
        
    def _get_remotes_config(self):
        config = self.config['intertrac']
        intertracs = {}
        for key, val in config.options():
            m = self.defin_patt.match(key)
            if m:
                prefix, attribute = m.groups()
                intertrac = intertracs.setdefault(prefix, {})
                intertrac[attribute] = val
            else:
                intertracs[key] = val
        
        return intertracs

    def _get_rtccs_config(self):
        config = self.config['remoteticketconditionalcreate']
        rtccs = {}
        for key, val in config.options():
            m = self.defin_patt.match(key)
            if m:
                prefix, attribute = m.groups()
                rtcc = rtccs.setdefault(prefix, {})
                rtcc[attribute] = val
            else:
                rtccs[key] = val
        
        return rtccs
