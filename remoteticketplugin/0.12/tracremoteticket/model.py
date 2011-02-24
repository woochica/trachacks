import socket
import xmlrpclib

from trac.resource import ResourceNotFound
from trac.ticket.api import TicketSystem
from trac.util.datefmt import (datetime, timedelta,
                               from_utimestamp, parse_date, to_utimestamp, 
                               utc)
from trac.util.text import empty
from trac.web.href import Href

from tracremoteticket.api import RemoteTicketSystem

__all__ = ['RemoteTicket']

class RemoteTicket(object):
    '''Local proxy for a ticket in a remote Trac system.
    '''
    # All fields from Trac ticket table except id
    remote_fields = ['time', 'changetime', 'component', #'severity', 
                     'priority', 'owner', 'reporter', 'cc',
                     'version', 'milestone', 'status', 'resolution',
                     'summary', 'description', 'keywords',
                     ]
    
    table_fields  = remote_fields + ['cachetime', 'remote_name', 'id']
    cachetime_pos = -3
    
    def __init__(self, env, remote_name, tkt_id, refresh=False):
        self.env = env
        self.remote_name = remote_name
        self.id = int(tkt_id)
        self.fields = [f for f in TicketSystem(self.env).get_ticket_fields()
                         if f['name'] in RemoteTicket.remote_fields]
        self.time_fields = [f['name'] for f in self.fields if 
                                      f['type'] == 'time']
        self.values = {}
        
        if not refresh:
            self._fetch_ticket()
        else:
            self._refresh_ticket()
        
    def _fetch_ticket(self):
        rts = RemoteTicketSystem(self.env)
        db = self.env.get_read_db()
        cursor = db.cursor()
        
        # Try to retrieve remote ticket from cache
        cursor.execute('''SELECT %s FROM remote_tickets 
                       WHERE remote_name=%%s and id=%%s
                       ''' % (', '.join(self.table_fields)),
                       (self.remote_name, self.id))
        row = cursor.fetchone()
        
        # Remote ticket not in cache
        if not row:
            self._refresh_ticket()
        
        self._cachetime = from_utimestamp(row[self.cachetime_pos])
        ttl = timedelta(seconds=int(rts.cache_ttl) // 1000, 
                        microseconds=int(rts.cache_ttl) % 1000 * 1000)
        
        # Cached remote ticket is too old
        if self._cachetime < datetime.now(utc) - ttl:
            self._refresh_ticket()
        
        # Cached ticket is valid, populate instance
        for name, value in zip(self.remote_fields, row):
            if name in self.time_fields:
                self.values[name] = from_utimestamp(value)
            elif value is None:
                self.values[name] = empty
            else:
                self.values[name] = value
        
    def _refresh_ticket(self):
        rts = RemoteTicketSystem(self.env)
        remote_trac = rts.get_remote_trac(self.remote_name)['url']
        xmlrpc_addr = Href(remote_trac).rpc()
        server = xmlrpclib.ServerProxy(xmlrpc_addr)
        
        try:
            tkt_vals = server.ticket.get(self.id)
        except xmlrpclib.ProtocolError, e:
            msg = ("Could not contact remote Trac '%s' at %s. "
                   "Received error %s, %s")
            log = ("XML-RPC ProtocolError contacting Trac %s at %s, "
                   "errcode=%s, errmsg='%s'")
            args = (self.remote_name, xmlrpc_addr, e.errcode, e.errmsg)
            self.env.log.warn(log, *args)
            raise ResourceNotFound(msg % args, "Uncontactable server")
        except xmlrpclib.Fault, e:
            msg = ("Could not retrieve remote ticket %s:#%s."
                   "Received fault %s, %s")
            log = ("XML-RPC Fault contacting Trac %s at %s, "
                   "faultCode=%s, faultString='%s'")
            args = (self.remote_name, self.id, e.faultCode, e.faultString)
            self.env.log.warn(log, *args)
            raise ResourceNotFound(msg % args, "Remote ticket unavailable")
        except socket.error, e:
            msg = ("Could not connect to remote Trac '%s' at %s. "
                   "Reason: %s")
            log = ("Network error connecting to remote Trac '%s' at '%s'. "
                   "Error: %s")
            args = (self.remote_name, xmlrpc_addr, e.args)
            self.env.log.warn(log, *args)
            raise ResourceNotFound(msg % args, "Network error")
        except Exception,e:
            msg = ("Unknown exception contacting remote Trac '%s' at %s. "
                   "Exception args: %s %s %s")
            args = (self.remote_name, xmlrpc_addr, e, type(e), e.args)
            self.env.log.error(msg, *args)
            raise
        
        # Convert from DateTime used by xmlrpclib to datetime used by trac
        for k in self.time_fields:
            tkt_vals[3][k] = parse_date(tkt_vals[3][k].value, utc)

        self.values.update(tkt_vals[3])
        self._cachetime = datetime.now(utc)
        self.save()
    
    def __getitem__(self, name):
        return self.values.get(name)
    
    def __setitem__(self, name, value):
        self.values[name] = value
    
    def populate(self, values):
        field_names = [f['name'] for f in self.fields 
                                 if f['name'] in values]
        for name in field_names:
            self[name] = values.get(name, '')
            
    def save(self, when=None):
        if when is None:
            when = self._cachetime
        when_ts = to_utimestamp(when)
        
        # Build the update/insert sequences
        # NB The ordering means the same sequences may be reused in both cases
        field_names = self.table_fields
        values_dict = dict(self.values)
        values_dict.update({'time': to_utimestamp(values_dict['time']),
                            'changetime': 
                                    to_utimestamp(values_dict['changetime']),
                            'cachetime': when_ts, 
                            'remote_name': self.remote_name, 
                            'id': self.id})
        values = [values_dict[name] for name in field_names]
        
        @self.env.with_transaction()
        def do_save(db):
            cursor = db.cursor()
            # Update the existing entry (if any)
            sql = ('''UPDATE remote_tickets SET %s
                   WHERE remote_name=%%s and id=%%s''' %
                   ','.join('%s=%%s' % name for name in field_names[:-2]))
            cursor.execute(sql, values)
            
            # If a row was updated then our work is done
            if cursor.rowcount > 0:
                return
            
            # If no rows were updated then this remote ticket is new to us
            sql = ('''INSERT INTO remote_tickets (%s) VALUES (%s)''' %
                   (','.join(field_names),  
                    ','.join(['%s'] * len(field_names))))
            cursor.execute(sql, values)
    
    def delete(self, db=None):
        @self.env.with_transaction(db)
        def do_delete(db):
            cursor = db.cursor()
            cursor.execute('''DELETE FROM remote_tickets 
                           WHERE remote_name=%s AND id=%s
                           ''',
                           (self.remote_name, self.id))
