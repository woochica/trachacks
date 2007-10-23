from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.ticket import ITicketCustomFieldValues

class ClientsList(Component):
    implements(ITicketCustomFieldValues)
    
    def __init__(self):
        pass
    def get_values(self):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT name FROM client")
        rv = []
        for name in cursor:
          rv.append((name,None))
        return rv

