from time import time
from trac.ticket.notification import TicketNotifyEmail
from trac.ticket import Ticket
from trac.ticket.web_ui import TicketModule

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

    def save_ticket(self, tckt, db, msg):
        # determine sequence number... 
        cnum = 0
        tm = TicketModule(self.env)
        for change in tm.grouped_changelog_entries(tckt, db):
            if change['permanent']:
                cnum += 1

        tckt.save_changes(self.authname, msg, self.now, db, cnum+1)
        db.commit()
        
        tn = TicketNotifyEmail(self.env)
        tn.notify(tckt, newticket=0, modtime=self.now)
        self.now += 1
        

    def start_work(self, ticket):

        if not self.can_work_on(ticket):
            return False

        # If the ticket is closed, we need to reopen it.
        db = self.env.get_db_cnx()
        tckt = Ticket(self.env, ticket, db)

        if 'closed' == tckt['status']:
            tckt['status'] = 'reopened'
            tckt['resolution'] = ''
            self.save_ticket(tckt, db, 'Automatically reopening in order to start work.')

            # Reinitialise for next test
            db = self.env.get_db_cnx()
            tckt = Ticket(self.env, ticket, db)

            
        if self.authname != tckt['owner']:
            tckt['owner'] = self.authname
            if 'new' == tckt['status']:
                tckt['status'] = 'assigned'
            else:
                tckt['status'] = 'new'
            self.save_ticket(tckt, db, 'Automatically reassigning in order to start work.')

            # Reinitialise for next test
            db = self.env.get_db_cnx()
            tckt = Ticket(self.env, ticket, db)


        if 'assigned' != tckt['status']:
            tckt['status'] = 'assigned'
            self.save_ticket(tckt, db, 'Automatically accepting in order to start work.')
                
        now = int(time())
        sql = "INSERT INTO work_log (user, ticket, lastchange, starttime, endtime) VALUES ('%s', %s, %s, %s, %s)" % \
              (self.authname, ticket, now, now, 0)
        cursor = db.cursor()
        cursor.execute(sql)
        

    def who_is_working_on(self, ticket):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT user,starttime FROM work_log WHERE ticket=%s AND endtime=0', (ticket,))
        try:
            who,since = cursor.fetchone()
            return who,since
        except:
            pass
        return None,None

    def who_last_worked_on(self, ticket):
        pass

    def get_latest_task(self):
        if self.authname == 'anonymous':
            return None

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT MAX(lastchange) FROM work_log WHERE user=%s', (self.authname,))
        row = cursor.fetchone()
        if not row or not row[0]:
            return None
    
        lastchange = row[0]
    
        task = {}
        cursor.execute('SELECT user,ticket,lastchange,starttime,endtime FROM work_log '
                       'WHERE user=%s AND lastchange=%s', (self.authname, lastchange))

        for user,ticket,lastchange,starttime,endtime in cursor:
            task['user'] = user
            task['ticket'] = ticket
            task['lastchange'] = lastchange
            task['starttime'] = starttime
            task['endtime'] = endtime
        return task
    
    def get_active_task(self):
        task = self.get_latest_task()
        if not task.has_key('endtime'):
            return None

        if task['endtime'] > 0:
            return None

        return task
