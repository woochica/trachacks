
from datetime import datetime, timedelta
from decimal import Decimal

from trac.core import *
from trac.ticket.api import ITicketChangeListener
from trac.ticket.query import Query
from trac.db import get_column_names
from trac.config import Option

from model import Availability, Availabilities


class TicketChangeListener(Component):
    """Ticket change listener triggering re-scheduling."""

    implements(ITicketChangeListener)
    
    def ticket_created(self, ticket):
        """Called when a ticket is created."""
        scheduler = Scheduler()
        scheduler.schedule(self.env);
            
    def ticket_changed(self, ticket, comment, author, old_values):
        """Called when a ticket is modified.
       
        `old_values` is a dictionary containing the previous values of the
        fields that have changed.
        """
        scheduler = Scheduler()
        scheduler.schedule(self.env, self.config);

    def ticket_deleted(self, ticket):
        """Called when a ticket is deleted."""
        scheduler = Scheduler()
        scheduler.schedule(self.env, self.config);


class Scheduler:
    """Ticket Scheduler"""
    
    def schedule(self, env, config):
        """Schedules all tickets"""

        db = env.get_db_cnx()

        self.availabilities =  Availabilities.get(db)        
        
        cursor = db.cursor()

        where = config.get("scheduling-tools", "schedule-tickets", "t.STATUS<>'closed' AND t.STATUS<>'resolved'")
        orderBy = config.get("scheduling-tools", "schedule-order", "m.due ASC, t.PRIORITY ASC, t.ID ASC")
        
        cursor.execute("SELECT t.ID,t.STATUS,t.OWNER,c.VALUE AS ESTIMATEDHOURS,start.VALUE AS STARTDATE,due.VALUE AS DUEDATE "+
                       "FROM TICKET t "+
                       "JOIN TICKET_CUSTOM c ON c.TICKET=t.ID AND c.NAME='estimatedhours' "+
                       "JOIN TICKET_CUSTOM start ON start.TICKET=t.ID AND start.NAME='startdate' "+
                       "JOIN TICKET_CUSTOM due ON due.TICKET=t.ID AND due.NAME='duedate' "+
                       "JOIN MILESTONE m ON m.NAME=t.MILESTONE "+
                       "WHERE "+where+" ORDER BY "+orderBy, None)
        now = datetime.now()
        now = datetime(now.year, now.month, now.day, now.hour)
        
        dates = {}
        
        for t in cursor:

            id = t[0]
            status = t[1]
            owner = t[2]
            est = t[3]
            if not est:
                continue
            oldstart = datetime.strptime(t[4], "%Y-%m-%d %H:%M:%S")
            olddue = datetime.strptime(t[5], "%Y-%m-%d %H:%M:%S")
            
            if owner in dates:
                date = dates[owner]
            else:
                date = now

            startdate,date = self.calcDue(owner, date, int(est))
            if oldstart > now:
                self.update(db, id, "startdate", startdate)
            
            if olddue >= now:
                dates[owner] = date
                self.update(db, id, "duedate", date)
            else:
                self.update(db, id, "duedate", now)

        db.commit()

        cursor.close()
        
    def calcDue(self, owner, date, hours):
        if hours==0:
            return date, date
            
        s, e = self.workingTime(date.date(), owner)
        start=None
        while True:
            workHours = (e-date).days*24+(e-date).seconds/(60*60)
            if workHours>0 and start is None:
                start = date
            hours -= max(0, workHours)
            if hours>0:
                date += timedelta(days=1)
                date,e = self.workingTime(date.date(), owner)
            else:
                return start, e+timedelta(hours=hours)

    def workingTime(self, date, owner):
        found = None
        for av in self.availabilities:
            if av.resources!="" and av.resources.find(owner)==-1:
                continue
            if av.weekdays.find(str(date.weekday()))==-1:
                continue
            if av.validFrom!="" and datetime.strptime(av.validFrom, "%Y-%m-%d").date() > date:
                continue
            if av.validUntil!="" and datetime.strptime(av.validUntil, "%Y-%m-%d").date() < date:
                continue
            found = av

        if found is None:
            return datetime(date.year, date.month, date.day, 0), datetime(date.year, date.month, date.day, 0)
        return datetime(date.year, date.month, date.day, int(found.workFrom)), datetime(date.year, date.month, date.day, int(found.workUntil))
            
        
    def update(self, db, id, field, value):

        update = db.cursor()
        update.execute("UPDATE TICKET_CUSTOM SET value=%s WHERE TICKET=%s AND NAME=%s",
                       (value, id, field))
        if update.rowcount==0:
            update.execute("INSERT INTO TICKET_CUSTOM (TICKET,NAME,VALUE) VALUES (%s, %s, %s)",
                           (id, field, value))
        update.close()
        