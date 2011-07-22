from trac.core import Component, implements
from trac.ticket.api import ITicketChangeListener
from trac.config import Option

class TicketConditionalCreationStatus(Component):
    implements(ITicketChangeListener)
 
    unowned = {}
    owned = {}

    def __init__(self):
        criteria = self._ccs_config('criteria');
        for c in (x.strip() for x in criteria.split(',')):
            self.unowned = self._ccs_parse(self.unowned, c, 'unowned')
            self.owned = self._ccs_parse(self.owned, c, 'owned')

    def ticket_created(self, ticket):
        self._ccs_choosestatus(ticket)

    def ticket_changed(self, ticket, comment, author, old_values):
        if 'status' in old_values and old_values['status'] == 'closed' and \
           ticket['status'] == 'new':
            self._ccs_choosestatus(ticket)

    def ticket_deleted(self, ticket):
        pass 

    def _ccs_choosestatus(self, ticket):
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

    def _ccs_newstatus(self, criteria, ticket):
        for criterium, values in criteria.items():
            for value, newstatus in values.items():
                if ticket[criterium] == value:
                    return newstatus
        return None

    def _ccs_parse(self, criteria, criterium, kind):
        config = self._ccs_config('%s.%s' % (criterium, kind))
        if config:
            for part in (x.strip() for x in config.split(',')):
                criteria = self._ccs_parse_one(criteria, criterium, part)
        return criteria

    def _ccs_parse_one(self, criteria, criterium, config):
        try:
            values, state = [x.strip() for x in config.split('->')]
        except ValueError:
            raise Exception('Bad option "%s"' % (config, ))
        for v in (x.strip() for x in values.split('|')):
            if not criterium in criteria:
                   criteria[criterium] = {}
            criteria[criterium][v] = state
        return criteria

    def _ccs_config(self, varname):
        return self.config.get('ticketconditionalcreationstatus', varname, '')

