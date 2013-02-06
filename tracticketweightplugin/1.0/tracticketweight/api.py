'''
Created on Feb 4, 2013

@author: Zack Shahan
'''

from trac.core import Component, implements
from trac.ticket.api import ITicketChangeListener
import re

class TracTicketWeight(Component):
    implements(ITicketChangeListener)

    def __init__(self):
        self.defin_patt = re.compile(r'(\w+)\.(\w+)')
        self.config_reporter = self._weight_config('reporter')
        self.config_owner = self._weight_config('owner')
        self.config_owner_hours_cfield = self._weight_config('owner_hours_cfield')
        self.cfields_reporter = self._ticket_custom_config('reporter')
        self.cfields_owner = self._ticket_custom_config('owner')
        if self.config_owner_hours_cfield['owner_hours_cfield']:
            self.cfield = self.config_owner_hours_cfield['owner_hours_cfield']
    def ticket_created(self, ticket):
        owner = 0
        reporter = 0
        if self.config_owner:
            owner = self._weight_counter(ticket,
                                         self.config_owner,
                                         self.cfields_owner)
        if self.config_reporter:
            reporter = self._weight_counter(ticket,
                                            self.config_reporter,
                                            self.cfields_reporter)
        with self.env.db_transaction as db:
            cursor = db.cursor()
            if reporter != 0:
                cursor.execute("""update ticket_custom set value = %s 
                                  where ticket = %s and name = 'weight_reporter'""",
                               (reporter, ticket.id))
            if owner != 0:
                cursor.execute("""update ticket_custom set value = %s 
                                  where ticket = %s and name = 'weight_owner'""",
                               (owner, ticket.id))
        
        if self.cfield:  
            self._owner_hours_set()
        
    def _weight_counter(self, ticket, type, cfields):
        weight_list = {}
        total_weight = 0
        for x in cfields:
            cfield = cfields[x]
            weight_list[cfield] = self._weight_parse(cfield, ticket)
        for x in weight_list.values():
            total_weight = int(total_weight) + int(x)
        return total_weight

    def ticket_changed(self, ticket, comment, author, old_values):
        if self.config_owner:
            owner = self._weight_counter(ticket,
                                         self.config_owner,
                                         self.cfields_owner)
        if self.config_reporter:
            reporter = self._weight_counter(ticket,
                                            self.config_reporter,
                                            self.cfields_reporter)
        with self.env.db_transaction as db:
            cursor = db.cursor()
            if reporter != 0:
                cursor.execute("""update ticket_custom set value = %s 
                                  where ticket = %s and name = 'weight_reporter'""",
                               (reporter, ticket.id))
            if owner != 0:
                cursor.execute("""update ticket_custom set value = %s 
                                  where ticket = %s and name = 'weight_owner'""",
                               (owner, ticket.id))
        if self.cfield:  
            self._owner_hours_set(ticket)
        
    def _owner_hours_set(self, ticket):
        with self.env.db_transaction as db:
            cursor = db.cursor()
            cursor.execute("""select tc.value from ticket_custom as tc 
                              join ticket as t on t.id = tc.ticket 
                              where t.status != 'closed' and tc.name = %s 
                              and tc.value != '' and t.owner = %s""",
                              (self.cfield, ticket.values['owner']))
            result = ','.join(rec[0] for rec in cursor.fetchall())
        if result:
            hours_min = 0
            hours_max = 0
            hours = [x.split('-') for x in result.split(',')]
            for x in hours:
                if '>' in x[0] or len(x) < 2:
                    x[0] = x[0].strip('>')
                    x.append(x[0])
                hours_min = hours_min + int(x[0])
                hours_max = hours_max + int(x[1])
        with self.env.db_transaction as db:
            cursor = db.cursor()
            cursor.execute("""replace into session_attribute (sid,authenticated,name,value) 
                              values (%s,'0','weight_hours_min',%s)""",
                              (ticket.values['owner'], hours_min))
            cursor.execute("""replace into session_attribute (sid,authenticated,name,value) 
                              values (%s,'0','weight_hours_max',%s)""",
                              (ticket.values['owner'], hours_max))
        
    #===========================================================================
    # def _owner_hours_get(self):
    #    with self.env.db_transaction as db:
    #        # user = "zack"
    #        cursor = db.cursor()
    #        cursor.execute("""select sid,name,value from session_attribute 
    #                          where name = 'weight_hours_min'
    #                          or name = 'weight_hours_max'""")
    #        for sid, name, value in cursor.fetchall():
    #            hours = []
    #            if name == 'weight_hours_min':
    #                hours_min = value 
    #            elif name == 'weight_hours_max':
    #                hours_max = value
    #                
    #        print hours
    #===========================================================================

    def _weight_config(self, user):
        config = {}
        for key, val in self.config['weight'].options():
            if key == user:
                config[key] = val
        return config

    def _weight_parse(self, cfield, ticket):
        cfield_option = self.config.get('ticket-custom', '%s' % cfield)
        if cfield_option == 'select':
            result = self._weight_parse_select(cfield)
        elif cfield_option == 'text':
            result = ticket.values[cfield]
        
        weight = 0
        if result:
            for x in result:
                if cfield in ticket.values and \
                result[x] == ticket.values[cfield]:
                    weight = x
                    break
        return weight
            
    def _weight_parse_select(self, cfield):
        fields = self.config.get('ticket-custom', '%s.options' % cfield)
        x = 0
        items = {}
        for item in (x.strip() for x in fields.split('|')):
            if item != '':
                items[x] = item
                x += 1
        return items

    def _ticket_custom_config(self, val):
        x = 0
        option = {}
        for key, value in self.config['ticket-custom'].options():            
            if key.endswith('.weight') and value == val:
                option[x] = key.split('.', 1)[0]
                x += 1
        return option
