from datetime import datetime

from trac.ticket.api import TicketSystem
from trac.util.datefmt import utc

class RemoteTicket(object):
    '''Local proxy for a ticket in a remote Trac system.
    '''
    remote_fields = ['summary', 'status', 'type', 'resolution']
    
    def __init__(self, env, remote_name, id):
        self.env = env
        self.remote_name = remote_name
        self.id = id
        self.fields = [f for f TicketSystem(self.env).get_ticket_fields()
                         if f['name'] in remote_fields]
        self.values = {}
    
    def __getitem__(self, name):
        return self.values.get(name)
    
    def __setitem__(self, name, value):
        self.values[name] = value
    
    def populate(self, values):
        field_names = [f['name'] for f in self.fields 
                                 if f['name'] in values]
        for name in field_names:
            self[name] = values.get(name, '')
        
    def insert(self, when=None, db=None):
        if when is None:
            when = datetime.now(utc)
        
        values = dict(self.values)
        std_fields = [f['name'] for f in self.fields 
                                if f['name'] in self.values]
        
        @self.env.with_transaction(db)
        def do_insert(db):
            cursor = db.cursor()
            cursor.execute('INSERT INTO remote_tickets (%s) VALUES (%s)',
                           % (','.join(std_fields),
                              ','.join('%s' for _ in std_fields)),
                           [values[name] for name in std_fields])
        
        return self.id
    
    def delete(self, db=None):
        @self.env.with_transaction(db)
        def do_delete(db):
            cursor = db.cursor()
            cursor.execute('''DELETE FROM remote_tickets 
                           WHERE remote_name=%s AND id=%s
                           ''',
                           (self.remote_name, self.id))
