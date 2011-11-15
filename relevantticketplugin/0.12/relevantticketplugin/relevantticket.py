# -*- coding: utf-8 -*-
import re

from datetime import datetime

from trac.config import Option
from trac.core import *
from trac.ticket.api import ITicketChangeListener, TicketSystem
from trac.ticket.model import Ticket
from trac.util.datefmt import to_utimestamp, utc

class RelevantTicketPlugin(Component):
    implements(ITicketChangeListener)
    
    tfield = Option('relevant_ticket', 'target_field', 'relevant_tickets',
                          doc="""The field name for inputing IDs of relevant ticket.""")
    
    def _check_field_existance(self):
        
        ticket_system = TicketSystem(self.env)
        custom_fields = ticket_system.get_custom_fields()
        
        for custom_field in custom_fields:
            if custom_field['type'] == 'text':
                if custom_field['name'] == self.tfield:
                    return True
        
        return False
        
    def _get_custom_value(self, id, field, db):
        
        row = None
        
        cursor = db.cursor()
        cursor.execute("""
            SELECT value FROM ticket_custom WHERE name=%s AND ticket=%s
            """, (field, id))
        row = cursor.fetchone()
        
        if not row:
            return ''
        else:
            return row[0]
        
    def _get_id_list(self, value):
        
        format = re.compile('\#[0-9]+$')
        
        candidates = [candidate.strip() for candidate in value.split(',')]
        id_list = [candidate for candidate in candidates if format.match(candidate)]
        
        return id_list
        
    def _get_comment_num(self, id, db):
        
        num = 0
        
        cursor = db.cursor()
        cursor.execute("""
            SELECT DISTINCT tc1.time,COALESCE(tc2.oldvalue,'')
            FROM ticket_change AS tc1
              LEFT OUTER JOIN
                (SELECT time,oldvalue FROM ticket_change
                 WHERE field='comment') AS tc2
              ON (tc1.time = tc2.time)
            WHERE ticket=%s ORDER BY tc1.time DESC
            """, (id,))
        for ts, old in cursor:
            try:
                num += int(old.rsplit('.', 1)[-1])
                break
            except ValueError:
                num += 1
                
        return str(num + 1)
        
    def ticket_created(self, ticket):
        
        field_exists = self._check_field_existance()
        if not field_exists:
            self.log.warning('Custom field(%s) does not exist.' % self.tfield)
            return
        
        if not ticket.values.has_key(self.tfield):
            self.log.info('Ticket(%s) does not have a value of %s.' % ('#' + str(ticket.id), self.tfield))
            return
        
        new_id_list = self._get_id_list(ticket.values[self.tfield])
        
        commit = False
        
        when = datetime.now(utc)
        when_ts = to_utimestamp(when)
        
        db = self.env.get_db_cnx()
        for tid in new_id_list:
            
            try:
                tticket = Ticket(self.env, int(tid[1:]), db)
            except:
                self.log.warning('Ticket(%s) does not exist.' % tid)
                continue
            
            if tticket.values.has_key(self.tfield):
                old_tvalue = tticket.values[self.tfield]
            else:
                old_tvalue = ''
            
            target_id_list = self._get_id_list(old_tvalue)
            
            if not '#' + str(ticket.id) in target_id_list:
                if old_tvalue.strip() == '':
                    new_tvalue = "#" + str(ticket.id)
                else:
                    new_tvalue = old_tvalue + ", #" + str(ticket.id)
                
                cursor = db.cursor()
                comment = 'updated by #' + str(ticket.id)
                comment_num = self._get_comment_num(tid[1:], db)
                
                if tticket.values.has_key(self.tfield):
                    cursor.execute("""
                        UPDATE ticket_custom SET value=%s WHERE name=%s AND ticket=%s
                        """, (new_tvalue, self.tfield, tid[1:]))
                else:
                    cursor.execute("""
                        INSERT INTO ticket_custom(ticket,name,value)
                        VALUES(%s,%s,%s)
                        """, (tid[1:], self.tfield, new_tvalue))
                    
                cursor.execute("""
                    INSERT INTO ticket_change(ticket,time,author,field,oldvalue,newvalue)
                    VALUES (%s,%s,%s,%s,%s,%s)
                    """, (tid[1:], when_ts, ticket.values['reporter'], self.tfield, old_tvalue, new_tvalue))
                cursor.execute("""
                    INSERT INTO ticket_change(ticket,time,author,field,oldvalue,newvalue)
                    VALUES (%s,%s,%s,'comment',%s,%s)
                    """, (tid[1:], when_ts, ticket.values['reporter'], comment_num, comment))
                
                commit = True
                self.log.info('Ticket(%s) is updated by RelevantTicketPlugin.' % tid)
                
        if commit:
            db.commit()
            
    def ticket_changed(self, ticket, comment, author, old_values):
        
        field_exists = self._check_field_existance()
        if not field_exists:
            self.log.warning('Custom field(%s) does not exist.' % self.tfield)
            return
        
        if not ticket.values.has_key(self.tfield):
            self.log.info('Ticket(%s) does not have a value of %s.' % ('#' + str(ticket.id), self.tfield))
            return
        
        new_id_list = self._get_id_list(ticket.values[self.tfield])
        
        commit = False
        
        when = datetime.now(utc)
        when_ts = to_utimestamp(when)
        
        db = self.env.get_db_cnx()
        for tid in new_id_list:
            
            try:
                tticket = Ticket(self.env, int(tid[1:]), db)
            except:
                self.log.warning('Ticket(%s) does not exist.' % tid)
                continue
            
            if tticket.values.has_key(self.tfield):
                old_tvalue = tticket.values[self.tfield]
            else:
                old_tvalue = ''
            
            target_id_list = self._get_id_list(old_tvalue)
            
            if not '#' + str(ticket.id) in target_id_list:
                if old_tvalue.strip() == '':
                    new_tvalue = "#" + str(ticket.id)
                else:
                    new_tvalue = old_tvalue + ", #" + str(ticket.id)
                
                cursor = db.cursor()
                comment = 'updated by #' + str(ticket.id)
                comment_num = self._get_comment_num(tid[1:], db)
                
                if tticket.values.has_key(self.tfield):
                    cursor.execute("""
                        UPDATE ticket_custom SET value=%s WHERE name=%s AND ticket=%s
                        """, (new_tvalue, self.tfield, tid[1:]))
                else:
                    cursor.execute("""
                        INSERT INTO ticket_custom(ticket,name,value)
                        VALUES(%s,%s,%s)
                        """, (tid[1:], self.tfield, new_tvalue))
                    
                cursor.execute("""
                    INSERT INTO ticket_change(ticket,time,author,field,oldvalue,newvalue)
                    VALUES (%s,%s,%s,%s,%s,%s)
                    """, (tid[1:], when_ts, author, self.tfield, old_tvalue, new_tvalue))
                cursor.execute("""
                    INSERT INTO ticket_change(ticket,time,author,field,oldvalue,newvalue)
                    VALUES (%s,%s,%s,'comment',%s,%s)
                    """, (tid[1:],when_ts,author,comment_num,comment))
                
                commit = True
                self.log.info('Ticket(%s) is updated by RelevantTicketPlugin.' % tid)
                
        if commit:
            db.commit()
            