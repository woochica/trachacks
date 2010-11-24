import xmlrpclib

from trac.ticket.api import TicketSystem
from trac.util.datefmt import datetime, parse_date, utc
from trac.web.href import Href

from tracremoteticket.api import RemoteTicketSystem
        
class RemoteTicket(object):
    '''Local proxy for a ticket in a remote Trac system.
    '''
    remote_fields = ['summary', 'status', 'type', 'resolution']
    
    def __init__(self, env, remote_name, tkt_id):
        self.env = env
        self.remote_name = remote_name
        self.id = int(tkt_id)
        self.fields = [f for f in TicketSystem(self.env).get_ticket_fields()
                         if f['name'] in RemoteTicket.remote_fields]
        self.values = {}
        self._fetch_ticket()
        
    def _fetch_ticket(self):
        # TODO Define and use method
        rts = RemoteTicketSystem(self.env)
        remote_trac = rts.get_remote_trac(self.remote_name)['url']
        server = xmlrpclib.ServerProxy(Href(remote_trac).rpc())
        multicall = xmlrpclib.MultiCall(server)
        
        try:
            tkt_vals = server.ticket.get(self.id)
        except xmlrpclib.Error, e:
            return
        
        # Convert from DateTime used by xmlrpclib to datetime used by trac
        for k in ['time', 'changetime']:
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
        # Build the update/insert sequences
        # NB The ordering means the same sequences may be reused in both cases
        field_names = self.remote_fields + ['cachetime', 'remote_name', 'id']
        values_dict = dict(self.values)
        values_dict.update({'cachetime': when, 'remote_name': self.remote_name, 
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
