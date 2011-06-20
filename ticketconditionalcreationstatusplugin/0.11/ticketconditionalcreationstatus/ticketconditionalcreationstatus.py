from trac.core import Component, implements
from trac.ticket.api import ITicketChangeListener
from trac.config import Option

class TicketConditionalCreationStatus(Component):
    implements(ITicketChangeListener)
 
    unowned = dict()
    owned = dict()

    def __init__(self):
        criteria = self.config.get('ticketconditionalcreationstatus', 'criteria', '');
        for c in (x.strip() for x in criteria.split(',')):
            config = self.config.get('ticketconditionalcreationstatus', '%s.unowned' % c, '')
            if config != '':
                self.unowned = self._ccs_parse(self.unowned, c, config)
            config = self.config.get('ticketconditionalcreationstatus', '%s.owned' % c, '')
            if config != '':
                self.owned = self._ccs_parse(self.owned, c, config)

    def ticket_created(self, ticket):
        status = None

        if ticket['owner']:
            status = self._ccs_newstatus(self.owned, ticket)

        if status is None:
            status = self._ccs_newstatus(self.unowned, ticket)

        if status is not None:
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute("update ticket set status=%s where id=%s", (status, ticket.id))
            db.commit()

    def ticket_changed(self, ticket, comment, author, old_values):
        pass

    def ticket_deleted(self, ticket):
        pass 

    def _ccs_parse(self, criteria, criterium, config):
        try:
            values, state = [x.strip() for x in config.split('->')]
        except ValueError:
            raise Exception('Bad option "%s"' % (config, ))
        for v in (x.strip() for x in values.split(',')):
            if not criterium in criteria:
                   criteria[criterium] = dict()
            criteria[criterium][v] = state
        return criteria
    
    def _ccs_newstatus(self, criteria, ticket):
        for criterium, values in criteria.items():
            for value, newstatus in values.items():
                if ticket[criterium] == value:
                    return newstatus
        return None
