# -*- coding: utf-8 -*-

from trac.ticket.notification import TicketNotifyEmail
from trac.ticket import Ticket
from trac.ticket.web_ui import TicketModule
from trac.util.datefmt import format_date, format_time, to_datetime

from util import pretty_timedelta

from datetime import datetime
from time import time


class WorkLogManager:
    env = None
    config = None
    authname = None
    explanation = None
    now = None
    
    def __init__(self, env, config, authname='anonymous'):
        self.env = env
        self.config = config
        self.authname = authname
        self.explanation = ""
        self.now = int(time()) - 1

    def get_explanation(self):
        return self.explanation
    
    def can_work_on(self, ticket):
        # Need to check several things.
        # 1. Is some other user working on this ticket?
        # 2. a) Is the autostopstart setting true? or
        #    b) Is the user working on a ticket already?
        # 3. a) Is the autoreassignaccept setting true? or
        #    b) Is the ticket assigned to the user?

        # 0. Are you logged in?
        if self.authname == 'anonymous':
            self.explanation = 'You need to be logged in to work on tickets.'
            return False
        
        # 1. Other user working on it?
        who,since = self.who_is_working_on(ticket)
        if who:
            if who != self.authname:
                self.explanation = 'Another user (%s) has been working on ticket #%s since %s' % (who, ticket, since)
            else:
                self.explanation = 'You are already working on ticket #%s' % (ticket,)
            return False

        # 2. a) Is the autostopstart setting true? or
        #    b) Is the user working on a ticket already?
        if not self.config.getbool('worklog', 'autostopstart'):
            active = self.get_active_task()
            if active:
                self.explanation = 'You cannot work on ticket #%s as you are currently working on ticket #%s. You have to chill out.' % (ticket, active['ticket'])
                return False
        
        # 3. a) Is the autoreassignaccept setting true? or
        #    b) Is the ticket assigned to the user?
        if not self.config.getbool('worklog', 'autoreassignaccept'):
            tckt = Ticket(self.env, ticket)
            if self.authname != tckt['owner']:
                self.explanation = 'You cannot work on ticket #%s as you are not the owner. You should speak to %s.' % (ticket, tckt['owner'])
                return False

        # If we get here then we know we can start work :)
        return True

    def save_ticket(self, tckt, msg):
        # determine sequence number... 
        cnum = 0
        tm = TicketModule(self.env)
        for change in tm.grouped_changelog_entries(tckt, None):
            if change['permanent']:
                cnum += 1
        nowdt = self.now
        nowdt = to_datetime(nowdt)
        tckt.save_changes(self.authname, msg, nowdt, cnum=str(cnum+1))
        ## Often the time overlaps and causes a db error,
        ## especially when the trac integration post-commit hook is used.
        ## NOTE TO SELF. I DON'T THINK THIS IS NECESSARY RIGHT NOW...
        #count = 0
        #while count < 10:
        #    try:
        #        tckt.save_changes(self.authname, msg, self.now, cnum=cnum+1)
        #        count = 42
        #    except Exception, e:
        #        self.now += 1
        #        count += 1
        
        tn = TicketNotifyEmail(self.env)
        tn.notify(tckt, newticket=0, modtime=nowdt)
        # We fudge time as it has to be unique
        self.now += 1
        

    def start_work(self, ticket):

        if not self.can_work_on(ticket):
            return False

        # We could just horse all the fields of the ticket to the right values
        # bit it seems more correct to follow the in-build state-machine for
        # ticket modification.

        # If the ticket is closed, we need to reopen it.
        tckt = Ticket(self.env, ticket)

        if 'closed' == tckt['status']:
            tckt['status'] = 'reopened'
            tckt['resolution'] = ''
            self.save_ticket(tckt, 'Automatically reopening in order to start work.')

            # Reinitialise for next test
            tckt = Ticket(self.env, ticket)

            
        if self.authname != tckt['owner']:
            tckt['owner'] = self.authname
            if 'new' == tckt['status']:
                tckt['status'] = 'accepted'
            else:
                tckt['status'] = 'new'
            self.save_ticket(tckt, 'Automatically reassigning in order to start work.')

            # Reinitialise for next test
            tckt = Ticket(self.env, ticket)


        if 'accepted' != tckt['status']:
            tckt['status'] = 'accepted'
            self.save_ticket(tckt, 'Automatically accepting in order to start work.')

        # There is a chance the user may be working on another ticket at the moment
        # depending on config options
        if self.config.getbool('worklog', 'autostopstart'):
            # Don't care if this fails, as with these arguments the only failure
            # point is if there is no active task... which is the desired scenario :)
            self.stop_work(comment='Stopping work on this ticket to start work on #%s.' % ticket)
            self.explanation = ''
 
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO work_log (worker, ticket, lastchange, starttime, endtime)
            VALUES (%s, %s, %s, %s, %s)
            """, (self.authname, ticket, self.now, self.now, 0))
        db.commit()
        
        return True

    
    def stop_work(self, stoptime=None, comment=''):
        active = self.get_active_task()
        if not active:
            self.explanation = 'You cannot stop working as you appear to be a complete slacker already!'
            return False

        if stoptime:
            if stoptime <= active['starttime']:
                self.explanation = 'You cannot set your stop time to that value as it is before the start time!'
                return False
            elif stoptime >= self.now:
                self.explanation = 'You cannot set your stop time to that value as it is in the future!'
                return False
        else:
            stoptime = self.now - 1

        stoptime = float(stoptime)
          
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('UPDATE work_log '
                       'SET endtime=%s, lastchange=%s, comment=%s '
                       'WHERE worker=%s AND lastchange=%s AND endtime=0',
                       (stoptime, stoptime, comment, self.authname, active['lastchange']))
        db.commit()
        
        plugtne = self.config.getbool('worklog', 'timingandestimation') and self.config.get('ticket-custom', 'hours')
        plughrs = self.config.getbool('worklog', 'trachoursplugin') and self.config.get('ticket-custom', 'totalhours')

        message = ''
        hours = '0.0'

        # Leave a comment if the user has configured this or if they have entered
        # a work log comment.
        if plugtne or plughrs:
            round_delta = float(self.config.getint('worklog', 'roundup') or 1)

            # Get the delta in minutes
            delta = float(int(stoptime) - int(active['starttime'])) / float(60)

            # Round up if needed
            delta = int(round((delta / round_delta) + float(0.5))) * int(round_delta)

            # This hideous hack is here because I don't yet know how to do variable-DP rounding in python - sorry!
            # It's meant to round to 2 DP, so please replace it if you know how.  Many thanks, MK.
            hours = str(float(int(100 * float(delta) / 60) / 100.0))

        if plughrs:
            message = 'Hours recorded automatically by the worklog plugin. %s hours' % hours
        elif self.config.getbool('worklog', 'comment') or comment:
            started = datetime.fromtimestamp(active['starttime'])
            finished = datetime.fromtimestamp(stoptime)
            message = '%s worked on this ticket for %s between %s %s and %s %s.' % \
                      (self.authname, pretty_timedelta(started, finished), \
                       format_date(active['starttime']), format_time(active['starttime']), \
                       format_date(stoptime), format_time(stoptime))
        if comment:
            message += "\n[[BR]]\n" + comment


        if plugtne or plughrs:
            if not message:
                message = 'Hours recorded automatically by the worklog plugin.'

            tckt = Ticket(self.env, active['ticket'])

            if plugtne:
                tckt['hours'] = hours
            self.save_ticket(tckt, message)
            message = ''

        if message:
            tckt = Ticket(self.env, active['ticket'])
            self.save_ticket(tckt, message)

        return True


    def who_is_working_on(self, ticket):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT worker,starttime FROM work_log WHERE ticket=%s AND endtime=0', (ticket,))
        try:
            who, since = cursor.fetchone()
            return who, float(since)
        except:
            pass
        return None, None

    def who_last_worked_on(self, ticket):
        return "Not implemented"

    def get_latest_task(self):
        if self.authname == 'anonymous':
            return None

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT MAX(lastchange) FROM work_log WHERE worker=%s', (self.authname,))
        row = cursor.fetchone()
        if not row or not row[0]:
            return None
    
        lastchange = row[0]
    
        task = {}
        cursor.execute('SELECT wl.worker, wl.ticket, t.summary, wl.lastchange, wl.starttime, wl.endtime, wl.comment '
                       'FROM work_log wl '
                       'LEFT JOIN ticket t ON wl.ticket=t.id '
                       'WHERE wl.worker=%s AND wl.lastchange=%s', (self.authname, lastchange))

        for user,ticket,summary,lastchange,starttime,endtime,comment in cursor:
            if not comment:
                comment = ''
            
            task['user'] = user
            task['ticket'] = ticket
            task['summary'] = summary
            task['lastchange'] = float(lastchange)
            task['starttime'] = float(starttime)
            task['endtime'] = float(endtime)
            task['comment'] = comment
        return task
    
    def get_active_task(self):
        task = self.get_latest_task()
        if not task:
            return None
        if not task.has_key('endtime'):
            return None

        if task['endtime'] > 0:
            return None

        return task

    def get_work_log(self, mode='all'):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        if mode == 'user':
            cursor.execute('SELECT wl.worker, s.value, wl.starttime, wl.endtime, wl.ticket, t.summary, t.status, wl.comment '
                           'FROM work_log wl '
                           'INNER JOIN ticket t ON wl.ticket=t.id '
                           'LEFT JOIN session_attribute s ON wl.worker=s.sid AND s.name=\'name\' '
                           'WHERE wl.worker=%s '
                           'ORDER BY wl.lastchange DESC', (self.authname,))
        elif mode == 'summary':
            cursor.execute('SELECT wl.worker, s.value, wl.starttime, wl.endtime, wl.ticket, t.summary, t.status, wl.comment '
                           'FROM (SELECT worker,MAX(lastchange) AS lastchange FROM work_log GROUP BY worker) wlt '
                           'INNER JOIN work_log wl ON wlt.worker=wl.worker AND wlt.lastchange=wl.lastchange '
                           'INNER JOIN ticket t ON wl.ticket=t.id '
                           'LEFT JOIN session_attribute s ON wl.worker=s.sid AND s.name=\'name\' '
                           'ORDER BY wl.lastchange DESC, wl.worker')
        else:
            cursor.execute('SELECT wl.worker, s.value, wl.starttime, wl.endtime, wl.ticket, t.summary, t.status, wl.comment '
                           'FROM work_log wl '
                           'INNER JOIN ticket t ON wl.ticket=t.id '
                           'LEFT JOIN session_attribute s ON wl.worker=s.sid AND s.name=\'name\' '
                           'ORDER BY wl.lastchange DESC, wl.worker')
        
        rv = []
        for user,name,starttime,endtime,ticket,summary,status,comment  in cursor:
            starttime = float(starttime)
            endtime = float(endtime)
            
            started = datetime.fromtimestamp(starttime)
            
            dispname = user
            if name:
                dispname = '%s (%s)' % (name, user)
            
            if not endtime == 0:
                finished = datetime.fromtimestamp(endtime)
                delta = 'Worked for %s (between %s %s and %s %s)' % \
                        (pretty_timedelta(started, finished),
                         format_date(starttime), format_time(starttime),
                         format_date(endtime), format_time(endtime))
            else:
                delta = 'Started %s ago (%s %s)' % \
                        (pretty_timedelta(started),
                         format_date(starttime), format_time(starttime))

            rv.append({'user': user,
                       'name': name,
                       'dispname': dispname,
                       'starttime': int(starttime),
                       'endtime': int(endtime),
                       'delta': delta,
                       'ticket': ticket,
                       'summary': summary,
                       'status': status,
                       'comment': comment})
        return rv
        