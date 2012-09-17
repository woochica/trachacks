# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 Bart Ogryczak
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import sys, traceback

HARD_DEADLINE_FIELD = 'hard_deadline1'
IMPACT_FIELD = 'impact'
NO_BACKLOG = 'no backlog'

class BacklogException(Exception): pass

class Backlog(object):
    "Class representing an Backlog"

    def __init__(self, env, id=None, name=None):
        """
        Constructor
        @param env: Trac environment
        @param id:  numeric id of the backlog
        @param name: textual name of the backlog
        
        Retrieves backlog either by id or name;
        Initializes empty object is nither is set.
        """
        self.env = env
        self.db = self.env.get_db_cnx()

        if name == NO_BACKLOG: name = None
        if id:
            self._fetch_by_id(id)
        elif name:
            self._fetch_by_name(name)

    def create(self, name):
        """
        Creates new backlog entry in DB.
        @param name: textual name of the backlog   
        """
        if not name or not name.strip():
            raise BacklogException("Backlog needs to have non-empty name")

        self.name = name
        self.id = self._get_free_id()
        if(not self.id): return None
        return self._create()

    def _create(self):
        "Performs actual insert in DB"
        try:
            cursor = self.db.cursor()
            id = self._get_free_id()
            sql = "INSERT INTO backlog (id, name) VALUES (%s, %s)"
            cursor.execute(sql, (self.id, self.name,))
            self.db.commit()
        except:
            self.env.log.error(traceback.format_exc())
            raise BacklogException("Failed to create new backlog")

        return self

    def _get_free_id(self):
        """
        Auto-increment emulation, as some DBs don't have it.
        """
        try:
            cursor = self.db.cursor()
            sql = "SELECT max(id) FROM backlog"
            cursor.execute(sql)  
            id = cursor.fetchone()[0] + 1
        except:
            self.env.log.error(traceback.format_exc())
            raise BacklogException("Failed to obtain next free id")    
        return id
    
    def _fetch_by_id(self, id):
        """
        Retrieves backlog data by id
        @param id:  numeric id of the backlog        
        """
        assert id, 'id not set'
        self.id = int(id)
        try:
            cursor = self.db.cursor()
            sql = "SELECT name, owner, description FROM backlog WHERE id = %s"
            cursor.execute(sql, (self.id,))
            self.name, self.owner, self.description = cursor.fetchone()
        except:
            self.env.log.error(traceback.format_exc())
            raise BacklogException("Failed to retrieve backlog with id=%s" % self.id)  
        
    def _fetch_by_name(self, name):
        """
        Retrieves backlog data by name
        @param name: textual name of the backlog  
        """
        try:
            cursor = self.db.cursor()
            sql = "SELECT id FROM backlog WHERE name = %s" 
            cursor.execute(sql, (name,))
            self.id = cursor.fetchone()[0]                                
        except:
            self.env.log.error(traceback.format_exc())
            raise BacklogException("Failed to retrieve backlog with name=%s" % name)
        self._fetch_by_id(self.id)
        
    def get_tickets(self, all_in_one=False):
        assert self.id, 'id not set'
        """
        Retrieves relevant data for tickets in backlog
        By default returns two list: prioritized and unprioritized tickets 
        @param all_in_one: should all tickets be returned in one list  
        """
        try:
            cursor = self.db.cursor()
            #get name
            columns = ['id', 'summary', 'component', 'description', 'version', 'type', 'milestone', 'owner', 'status', 'time', 'tkt_order', 'keywords']
            sql = """SELECT %s,tc.value as hard_deadline, tc2.value as impact
                     FROM  backlog_ticket b, ticket t  
                     LEFT OUTER JOIN ticket_custom tc 
                     ON t.id = tc.ticket
                     AND tc.name = '%s'
                     LEFT OUTER JOIN ticket_custom tc2 
                     ON t.id = tc2.ticket
                     AND tc2.name = '%s'
                     WHERE t.id = b.tkt_id 
                     AND b.bklg_id = %%s 
                     AND (b.tkt_order IS NULL OR b.tkt_order > -1)
                     ORDER BY b.tkt_order, t.time DESC""" % (','.join(columns), HARD_DEADLINE_FIELD, IMPACT_FIELD)
            columns.extend(('hard_deadline', 'impact'))
            self.env.log.info('GET_TICKETS sql = """%s"""' % sql)      
            cursor.execute(sql, (self.id,))            
            all_tickets = [dict(zip(columns, ticket)) for ticket in cursor]  #creating list of column:value dictionaries
            #self.env.log.info('ALL_TICKETS = %s'%all_tickets)
           
        except:
            self.env.log.error(traceback.format_exc())
            raise BacklogException("Failed to retrieve ticket data for backlog %s" % self.name) 
        
        if(all_in_one):  
                return all_tickets
            
        #splitting ordered and unordered
        ordered_tickets, unordered_tickets = [], []
        for ticket in all_tickets:
            (ordered_tickets if ticket['tkt_order'] is not None else unordered_tickets).append(ticket)            
        return ordered_tickets, unordered_tickets
    
    def set_ticket_order(self, order):
        """
        saves ticket priorities in the DB
        @param order: sequence of ticket IDs 
        """
        assert self.id, 'id not set'
        order = [ (self.id, int(tkt_id), tkt_order + 1) for (tkt_order, tkt_id) in enumerate(order)]                        
        # print 'order', order        
        try:
            cursor = self.db.cursor()       
            cursor.executemany('REPLACE INTO backlog_ticket (bklg_id, tkt_id, tkt_order) VALUES (%s, %s, %s)', order)
            self.db.commit()
        except:
            self.env.log.error(traceback.format_exc())
            raise BacklogException("Failed to save order for backlog %s" % self.name) 
            
    def add_ticket(self, tkt_id):
        """ 
        adds the ticket to this backlog, also removing it from previous backlog if any
        @param tkt_id: ticket's ID 
        """
        try:
            cursor = self.db.cursor()            
            cursor.execute('DELETE FROM backlog_ticket WHERE tkt_id = %s', (tkt_id,))       
            cursor.execute('INSERT INTO backlog_ticket (bklg_id, tkt_id) VALUES (%s, %s)', (self.id, tkt_id))
            self.db.commit()
        except:
            self.env.log.error(traceback.format_exc())
            raise BacklogException("Failed to add ticket %s to backlog %s" % (tkt_id, self.name)) 

    def reset_priority(self, tkt_id, only_if_deleted=False):
        """
        resets the ticket's priority to NULL (unordered)
        @param tkt_id: ID or sequence of IDs of ticket(s)
        @param only_if_deleted: reset the priority only if ticket was deleted as closed (archived)
        """
        try:
            cursor = self.db.cursor()
            sql = 'UPDATE backlog_ticket SET tkt_order = NULL WHERE tkt_id = %s'
            if(only_if_deleted):
                sql += ' AND tkt_order = -1'               
            try:
                tkt_ids = [(id,) for id in tkt_id]  # trying to iterate to see if it's a list
                cursor.executemany(sql, tkt_ids)
            except TypeError: #single id
                cursor.execute(sql, (tkt_id,))    
            self.db.commit()
        except:
            self.env.log.error(traceback.format_exc())
            raise BacklogException("Failed to reset priority for ticket(s) %s " % (tkt_id,))          
        
    def delete_ticket(self, tkt_id):
        """ 
        removes ticket from this backlog
        @param tkt_id: ID of ticket
        """
        if(not getattr(self, 'id')): 
            self.env.log.warn('trying to delete ticket from uninitialized backlog')
            return
        try:
            cursor = self.db.cursor()            
            cursor.execute('DELETE FROM backlog_ticket WHERE bklg_id = %s AND tkt_id = %s', (self.id, tkt_id))       
            self.db.commit()
        except:
            self.env.log.error(traceback.format_exc())
            raise BacklogException("Failed to delete ticket %s from backlog" % (tkt_id,))          

    def remove_closed_tickets(self):
        """
        hides (archives) all closed tickets in the current backlog
        """
        assert self.id, 'id not set'
        sql = """UPDATE backlog_ticket SET tkt_order = -1
                 WHERE bklg_id = %s
                 AND tkt_id IN (SELECT id FROM ticket
                  WHERE status = 'closed')"""
        try:
            cursor = self.db.cursor()
            cursor.execute(sql, (self.id,))
            self.db.commit() 
        except:
            self.env.log.error(traceback.format_exc())
            raise BacklogException("Failed to clean up closed tickets in backlog %s" % (tkt_id, self.name))
            
    def name2perm(self):
        """
        creates string appropriate for Trac's permission system from current backlog's name 
        """
        import re
        return re.sub('[^A-Z0-9]', '_', self.name.upper())

        
class BacklogList(object):
    "Class representing a sequence of all backlogs available in Trac"

    def __init__(self, env):
        """Initializes object with data fetched from the DB
        @param env: Trac environment
        """
        self.env = env
        try:
            db = env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute("SELECT id FROM backlog ORDER BY id")
            self.backlogs = (Backlog(env, row[0]) for row in cursor)
        except:
            self.env.log.error(traceback.format_exc())
            self.backlogs = ()

    def __iter__(self):
        "Returns iterator"
        return self.backlogs.__iter__()

