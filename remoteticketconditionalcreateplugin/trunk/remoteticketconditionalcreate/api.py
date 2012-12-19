'''
Created on Dec 3, 2012

@author: Zack Shahan
'''

from trac.core import Component, implements
from trac.ticket.api import ITicketChangeListener, ITicketManipulator
from trac.resource import ResourceNotFound
from tracrpc import *
from trac.web.href import Href
import xmlrpclib
import re
from urlparse import urlsplit

class RemoteTicketConditionalCreate(Component):
    implements(ITicketChangeListener,
               ITicketManipulator)

    rtype = {}
    rcomponent = {}
    rintertrac = {}
    lfield = {}
    rfield = {}

    def __init__(self):
        status = self._rtcc_config('status');
        lintertrac = self._rtcc_config('intertrac_name');
        self.lintertrac = lintertrac
        self._get_config(status)
        self._intertracs = self._get_remotes_config()
        
    def _get_config(self, status):
        for c in (x.strip() for x in status.split(',')):
            self.status = '%s' % (c)
            self.rtype = self._rtcc_config('%s.type' % (c))
            self.rcomponent = self._rtcc_config('%s.component' % (c))
            self.rintertrac = self._rtcc_config('%s.remote_intertrac' % (c))
            self.lfield = self._rtcc_config('%s.local_cfield' % (c))
            self.rfield = self._rtcc_config('%s.remote_cfield' % (c))
            self.ruser = self._rtcc_config('%s.xmlrpc_user' % (c))
            self.rpassword = self._rtcc_config('%s.xmlrpc_password' % (c))
            
    # create xmlrpc connection to remote intertrac    
    def _xmlrpc_connect(self, rintertrac):
        remote_trac = self._get_remote_trac(rintertrac)['url']
        addr_split = urlsplit(remote_trac)
        if self.ruser:
            final_url = ''.join((addr_split.scheme, '://', self.ruser, ':', self.rpassword, '@',
                                 addr_split.netloc, addr_split.path, '/login'))
        else:
            final_url = remote_trac
            
        xmlrpc_addr = Href(final_url).rpc()
        server = xmlrpclib.ServerProxy(xmlrpc_addr)
        
        return server
    
    # converts users in ticket to email addresses for remote intertrac
    def _get_email_addrs(self, user):
        addr_list = []
        EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
        sep = re.compile('[\s,]+')
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        for email in sep.split(user):
            if not EMAIL_REGEX.match(email):
                cursor.execute('select value from session_attribute where name = "email" and sid = %s',
                               (email,))
                result = ','.join(rec[0] for rec in cursor.fetchall())
                if not result:
                    result = email
            else:
                result = email
            addr_list.append(result)
        db.commit()
        final_addr_list = ','.join(addr_list)
        return final_addr_list


    # create the ticket on the specified intertrac
    def _create_remote_ticket(self, rintertrac, ticket):
        server = self._xmlrpc_connect(rintertrac)        
        tsummary = str(ticket.values['summary'])
        tdescription = str(ticket.values['description'])
        attrs = {
                'type': self.rtype,
                'status': 'new',
                'component': self.rcomponent,
                self.rfield : '%s:#%s' % (self.lintertrac, ticket.id),
                'reporter' : '%s' % (self._get_email_addrs(ticket.values['reporter'])),
                'cc' : '%s,%s' % (self._get_email_addrs(ticket.values['owner']),
                                  self._get_email_addrs(ticket.values['cc']))
            }
        
        rticket = server.ticket.create(tsummary, tdescription, attrs)
        return rticket
    
    # main routine. if status falls into this scope, create the remote ticket and
    # add the remote ticket link to the current ticket
    def ticket_changed(self, ticket, comment, author, old_values):
        self._get_config(ticket.values['status'])
        if 'status' in old_values and old_values['status'] != self.status:
            if 'status' in ticket.values and ticket.values['status'] == self.status:
                if not ticket.values[str(self.lfield)]:
                    rticket = self._create_remote_ticket(self.rintertrac, ticket)
                    self._update_intertrac_link(rticket, self.rintertrac, ticket)


    def ticket_created(self, ticket):
        pass 
    
    def ticket_deleted(self, ticket):
        pass
    
    def validate_ticket(self, req, ticket):
        # Make sure custom field is empty before we add the link
        if 'status' in ticket.values and ticket.values['status'] == self.status:
            if ticket.values[str(self.lfield)]:
                return [(None, "Cannot update ticket that has already been %s." % 
                         (self.status))]
        return []

    # add the intertrac link to the ticket
    def _update_intertrac_link(self, rticket, rintertrac, ticket):
        intertrac_link = '%s:#%s' % (rintertrac, rticket)
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('replace into ticket_custom values (%s,%s,%s)',
                       (ticket.id,
                        self.lfield,
                        intertrac_link))
        db.commit()

    def _rtcc_config(self, varname):
        config_option = self.config.get('remoteticketconditionalcreate', varname, '')
        if not config_option:
            raise ResourceNotFound("RemoteTicketConditionalCreate Plugin -- Missing option: %s" % (varname))
        return config_option
            
    
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
        
    def _get_remotes_config(self):
        '''Return dict of intertracs and intertrac aliases.
        
        Adapted from code in trac.wiki.intertrac.InterTracDispatcher
        '''
        defin_patt = re.compile(r'(\w+)\.(\w+)')
        config = self.config['intertrac']
        intertracs = {}
        for key, val in config.options():
            m = defin_patt.match(key)
            if m:
                prefix, attribute = m.groups()
                intertrac = intertracs.setdefault(prefix, {})
                intertrac[attribute] = val
            else:
                intertracs[key] = val
        
        return intertracs
