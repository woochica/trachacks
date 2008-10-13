# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         model.py
# Purpose:      The MMV Trac plugin db model module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
#----------------------------------------------------------------------------

"""Model classes for objects persisted in the database."""

import time

from trac.db import Table, Column, Index

from utils import *

class MMV_List(object):
    """Represents milestone list."""

    _schema = [
        Table('mmv_list', key='id')[
            Column('id', auto_increment=True), 
            Column('milestone'), 
            Column('startdate', type='int'), 
            Column('enddate', type='int'), 
            Column('enabled', type='int'), 
            Index(['milestone'])
        ],
        Table('mmv_history', key=('date', 'milestone'))[
            Column('date', type='int'), 
            Column('milestone'), 
            Column('due'), 
            Column('done'), 
            Index(['date', 'milestone'])
        ]
    ]

    def __init__(self, env, milestone=None):
        """Initialize a new entry with the specified attributes.

        To actually create this build log in the database, the `insert` method
        needs to be called.
        """
        self.env = env
        self.id = None
        self.milestone = milestone
        self.startdate = None
        self.enddate = None

    def delete(cls, env, milestone, db=None):
        """Remove the milestone from the database."""
        if not db:
            db = env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()
        cursor.execute("DELETE FROM mmv_list WHERE milestone=%s;", (milestone,))

        if handle_ta:
            db.commit()

    delete = classmethod(delete)

    def deleteAll(cls, env, db=None):
        """Remove the milestone from the database."""
        if not db:
            db = env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()
        cursor.execute("DELETE FROM mmv_list;")

        if handle_ta:
            db.commit()

    deleteAll = classmethod(deleteAll)

    def deleteAllHistory(cls, env, db=None):
        """Remove the milestone from the database."""
        if not db:
            db = env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()
        cursor.execute("DELETE FROM mmv_history;")

        if handle_ta:
            db.commit()

    deleteAllHistory = classmethod(deleteAllHistory)

    def insert(cls, env, milestone, startdate=None, enddate=None, enabled=False, db=None):
        """Insert a new milestone into the database."""
        if not db:
            db = env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False
            
        cursor = db.cursor()
        cursor.execute("INSERT INTO mmv_list "
                       "(milestone, startdate, enddate, enabled) VALUES (%s, %s, %s, %s);",
                       (milestone, startdate, enddate, int(enabled)))
        id = db.get_last_id(cursor, 'mmv_list')

        if handle_ta:
            db.commit()
        
        return id
    
    insert = classmethod(insert)
    

#    def getMilestones(cls, env, db=None):
#        """Retrieve from the database that match
#        the specified criteria.
#        """
#        if not db:
#            db = env.get_db_cnx()
#
#        cursor = db.cursor()
#
#        cursor.execute("SELECT milestone FROM mmv_list ORDER BY milestone;")
#        
#        return [m[0] for m in cursor.fetchall()]
#
#    getMilestones = classmethod(getMilestones)

    def getEnabledMilestones(cls, env, db=None):
        """Retrieve from the database that match
        the specified criteria.
        """
        if not db:
            db = env.get_db_cnx()

        cursor = db.cursor()

        cursor.execute("SELECT milestone FROM mmv_list "
                        "WHERE enabled = 1 ORDER BY milestone;")
        
        return [m[0] for m in cursor.fetchall()]

    getEnabledMilestones = classmethod(getEnabledMilestones)


    def getStartdate(cls, env, milestone, db=None):
        """Get start date of milestone.
        """
        if not db:
            db = env.get_db_cnx()

        cursor = db.cursor()

        cursor.execute("SELECT startdate FROM mmv_list WHERE milestone=%s LIMIT 1;", (milestone, ))
        
        row = cursor.fetchone()
        if not row or not row[0]:
            cursor.execute("SELECT min(time) FROM ticket WHERE milestone=%s LIMIT 1;", (milestone, ))
            row = cursor.fetchone()

        if row and not row[0]:
            return 0
        return row[0]

    getStartdate = classmethod(getStartdate)

    def getEnddate(cls, env, milestone, db=None):
        """Get end date of milestone.
        """
        if not db:
            db = env.get_db_cnx()

        cursor = db.cursor()

        cursor.execute("SELECT enddate FROM mmv_list  WHERE milestone=%s LIMIT 1;", (milestone, ))
        
        row = cursor.fetchone()
        if not row or not row[0]:
            cursor.execute("SELECT completed FROM milestone WHERE name=%s LIMIT 1;", (milestone, ))
            row = cursor.fetchone()

        if row and not row[0]:
            return int(time.time())
        return row[0]

    getEnddate = classmethod(getEnddate)


    def getStartdateFromDb(cls, env, milestone, db=None):
        """Get start date of milestone.
        """
        if not db:
            db = env.get_db_cnx()

        cursor = db.cursor()

        cursor.execute("SELECT startdate FROM mmv_list WHERE milestone=%s LIMIT 1;", (milestone, ))
        
        row = cursor.fetchone()
        if not row or not row[0]:
            return None
        return row[0]

    getStartdateFromDb = classmethod(getStartdateFromDb)

    def getEnddateFromDb(cls, env, milestone, db=None):
        """Get end date of milestone.
        """
        if not db:
            db = env.get_db_cnx()

        cursor = db.cursor()

        cursor.execute("SELECT enddate FROM mmv_list  WHERE milestone=%s LIMIT 1;", (milestone, ))
        
        row = cursor.fetchone()
        if not row or not row[0]:
            return None
        return row[0]

    getEnddateFromDb = classmethod(getEnddateFromDb)


    def getDue(cls, env, dateMin, dateMax, milestone, db=None):
        """Get due days data.
        """
        if not db:
            db = env.get_db_cnx()

        cursor = db.cursor()

        cursor.execute("SELECT date, due FROM mmv_history "
                        " WHERE milestone=%s AND date >= %s AND date <= %s;", 
                        (milestone, dateMin, dateMax, ))
        
        rows = cursor.fetchall()
        return rows

    getDue = classmethod(getDue)

    def getMaxHistoryDate(cls, env, milestone, db=None):
        """ get max history date for a milestone
        """
        if not db:
            db = env.get_db_cnx()

        cursor = db.cursor()

        cursor.execute("SELECT max(date) FROM mmv_history  "
                        "WHERE milestone = %s;", 
                        (milestone, ))
        
        row = cursor.fetchone()
        if not row[0]:
            return 0
        else:
            return int(row[0])

    getMaxHistoryDate = classmethod(getMaxHistoryDate)

    def addHistory(self, env, date, milestone, db=None):
        """Add due/done to history.
        """
        if not db:
            db = env.get_db_cnx()

        cursor = db.cursor()

        # get max_history_date
        max_history_date = self.getMaxHistoryDate(env, milestone)
        if date < max_history_date - 1: 
            # don't update stable history
            return
        # due
        dueDaysYest = self._getDueDays(date - 1, milestone, db)
        dueDays = self._getDueDays(date, milestone, db)

        # done
        doneDaysYest = self._getDoneDays(date - 1, milestone, db)
        doneDays = self._getDoneDays(date, milestone, db)


        # update the day before
        self._updateHistory(dueDaysYest, doneDaysYest, milestone, date - 1, db)

        # update the day
        self._updateHistory(dueDays, doneDays, milestone, date, db)

    def _updateHistory(self, dueDays, doneDays, milestone, date, db):
        if not db:
            db = env.get_db_cnx()

        cursor = db.cursor()

        exist = self._checkExist(milestone, date, db)
        if exist:
            # update
            cursor.execute("UPDATE mmv_history SET due = %s, done = %s "
                            "WHERE milestone = %s AND date = %s;", 
                            (dueDays, doneDays, milestone, date))
        else:
            # insert new
            cursor.execute("INSERT INTO mmv_history (due, done, milestone, date)"
                            "VALUES (%s, %s, %s, %s);", 
                            (dueDays, doneDays, milestone, date))

        db.commit()


    def _checkExist(self, milestone, date, db):
        """ check if history exist in db
        """
        cursor = db.cursor()

        cursor.execute("SELECT due, done FROM mmv_history  "
                        "WHERE milestone = %s AND date = %s LIMIT 1;", 
                        (milestone, date, ))
        
        if cursor.fetchone():
            return True
        else:
            return False


    def _getDueDays(self, date, milestone, db):
        """ Get total due days
        """
        cursor = db.cursor()

        # due
        sqlString = """
            SELECT tc.ticket, tc.name, tc.value 
            FROM ticket_custom tc, ticket t 
            WHERE tc.ticket = t.id 
            AND tc.name = 'duetime' 
            AND t.id IN (
                SELECT ta.id FROM 
                (SELECT id
                 FROM ticket
                 WHERE time < %(dateEndTime)s ) AS ta 
                 LEFT JOIN
                (SELECT DISTINCT B.ticket AS ticket, B.time AS time, A.newvalue AS newvalue
                     FROM ticket_change A,
                     (SELECT  ticket, max(time) AS time
                     FROM ticket_change 
                     WHERE field = 'status' 
                     AND time < %(dateEndTime)s
                     GROUP BY ticket 
                     ORDER BY ticket) AS B
                     WHERE A.ticket = B.ticket 
                     AND A.time = B.time
                     AND A.field = 'status'
                     AND newvalue IN ('closed','reopened') ) AS tb 
                 ON ta.id = tb.ticket
                 WHERE tb.newvalue != 'closed' OR tb.newvalue IS NULL
                 )  
            AND t.milestone = '%(milestone)s';
        """ % {'dateEndTime': (date + 1) * SECPERDAY, 'milestone':milestone, }

        cursor.execute(sqlString)
        rows = cursor.fetchall()

        # calculate total due days
        dueDays = 0
        for row in rows:
            dueDays += dueday(row[2])

        return dueDays

    def _getDoneDays(self, date, milestone, db):
        """ Get total done days
        """
        cursor = db.cursor()

        # done
        sqlString = """
            SELECT tc.ticket, tc.name, tc.value 
            FROM ticket_custom tc, ticket t 
            WHERE tc.ticket = t.id 
            AND tc.name = 'duetime' 
            AND t.id IN (
                SELECT ta.id FROM 
                (SELECT id
                 FROM ticket
                 WHERE time < %(dateEndTime)s ) AS ta 
                 LEFT JOIN
                (SELECT DISTINCT B.ticket AS ticket, B.time AS time, A.newvalue AS newvalue
                     FROM ticket_change A,
                     (SELECT  ticket, max(time) AS time
                     FROM ticket_change 
                     WHERE field = 'status' 
                     AND time < %(dateEndTime)s
                     GROUP BY ticket 
                     ORDER BY ticket) AS B
                     WHERE A.ticket = B.ticket 
                     AND A.time = B.time
                     AND A.field = 'status'
                     AND newvalue IN ('closed','reopened') ) AS tb 
                 ON ta.id = tb.ticket
                 WHERE tb.newvalue = 'closed'
                 )  
            AND t.milestone = '%(milestone)s';
        """ % {'dateEndTime': (date + 1) * SECPERDAY, 'milestone':milestone, }

        cursor.execute(sqlString)
        rows = cursor.fetchall()

        # calculate total done days
        doneDays = 0
        for row in rows:
            doneDays += dueday(row[2])

        return doneDays

schema = MMV_List._schema
schema_version = 2
