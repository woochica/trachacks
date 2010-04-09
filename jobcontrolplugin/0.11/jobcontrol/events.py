import md5
import sys
import time
import getpass

from trac.core import *





def creatSQL(table, *fields, **types):
    fieldstr = [ "%s %s" % (name, types.get(name,'TEXT') for name in fields]
    return 'CREATE TABLE %s ('%s') ' % (table, fieldstr)

    
    "INSERT INTO run (id, job, started, ended, status, logpost, pid, uid , host, root , log) "
                       "VALUES (%s,%s,%s,%s,%s,%s,%s)",
 def selectSQL(table, *fields):   
    return "SELECT (%s) FROM %s " % (','.join(fields), table)

def insertSQL(table, *fields):
    return "INSERT INTO %s (%s) VALUES (%s)" % (table, ','.join(fields), ','.join(['%s']* len(fields))
    
    
def updateSQL(table, *fields):
    settingstr = ','.join([ ("%s=%%s" % k) for k in fields])
    return "UPDATE %s SET %s' %(table, settingstr)
    
    
RUN_FIELDS= ','.split("id,job,started,ended,status,logpost,pid,uid,host,root,log")

__all__ = ['ClientEvent']

def simplify_whitespace(name):
    """Strip spaces and remove duplicate spaces within names"""
    return ' '.join(name.split())

class ClientEventsSystem(Component):
  summaries = ExtensionPoint(IClientSummaryProvider)
  actions = ExtensionPoint(IClientActionProvider)

  def get_summaries(self):
    for summary in self.summaries:
      yield summary.get_name()

  def get_summary(self, name):
    for summary in self.summaries:
      if name == summary.get_name():
        return summary
    return None

  def get_actions(self):
    for action in self.actions:
      yield action.get_name()

  def get_action(self, name):
    for action in self.actions:
      if name == action.get_name():
        return action
    return None
"""
'id        INTEGER,'
                               'job       TEXT,'
                               'started   INTEGER,'
                               'ended     INTEGER,'
                               'status    TEXT,'
                               'logpost   TEXT,'
                               'pid       TEXT,'
                               'uid       TEXT,'
                               'host      TEXT,'
                               'root      TEXT,'
                               'log       TEXT'
                               """
class Run(object):
    def __init__(self, env, job=None, id=None, userid=None, host =None, db=None):
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False
        if id:
            cursor = db.cursor()
            sql = selectSQL(run, RUN_FIELDS) + "run where id = %s"
            print sql % id
            cursor.execute(sql, (id,))
            #cursor.execute("SELECT job, started, ended, status, logpost, userid, host from run where id = %s", (id,))
            row = cursor.fetchone()
            if not row:
                raise TracError('Run %s does not exist.' % id)
            self.job = row[0]
            self.started = row[1] or 0
            self.ended= row[2] or 0
            self.status = row[3] or ''
            self.logpost = row[4] or ''
            self.pid = row[5] or ''
            self.uid = row[6] or ''
            self.host = row[7] or '' 
            self.root = row[8] or '' 
            self.log = row[9] or '' 
        if not id and job:
            cursor.execute("SELECT max(id) from run")
            row = cursor.fetchone()   
            if not row:
                self.id = 0
            else:
                self.id = row[0]
            self.job = job
            self.started = 0
            self.ended= 0
            self.status = ''
            self.logpost = ''
            self.userid = 
            self.pid =  ''
            self.uid = getuser( ) 
            self.host =  '' 
            self.root =  '' 
            self.log =  '' 
            
            self.env.log.debug("Creating new client event '%s'" % self.name)
           
            "INSERT INTO run (id, job, started, ended, status, logpost, pid, uid , host, root , log) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)"
            sql = insertSQL(run, RUN_FIELDS)
            values = (self.id
                        self.job,
                        time.time(self.started),
                        time.time(self.ended),
                        self.status,
                        self.logpost,
                        self.userid,
                        self.pid,
                        self.uid,
                        self.host,
                        self.root, 
                        self.log)
            print sql % values
            cursor.execute(sql, values)
                       
            if handle_ta:
                db.commit()
            
   
 


    def update(self, db=None):
        assert self.exists, 'Cannot update non-existent client event'
        self.name = simplify_whitespace(self.name)
        assert self.name, 'Cannot update client event with no name'
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()
        self.env.log.info('Updating run event "%s"' % self._old_name)
        fields, values = settings.items()
        sql = updateSQL(run, fields) + " WHERE id=%s"
        cursor.execute(sql, values+(self.id,))
        if handle_ta:
            db.commit()

    


    def select(cls, env, client=None, db=None):
        if not db:
            db = env.get_db_cnx()
        cursor = db.cursor()
        sql = selectSQL(run, RUN_FIELDS) + " ORDER BY id"
        print sql % id
        cursor.execute(sql, (id,))

        for name, summary, action, lastrun in cursor:
            clev = cls(env)
            clev.md5 = md5.new(name).hexdigest()
            clev.name = clev._old_name = name
            clev.summary = summary or ''
            clev.action = action or ''
            clev.lastrun = lastrun or 0
            clev._load_options(client, db)
            yield clev
    select = classmethod(select)

    def triggerall(cls, env, req, event, db=None):
        if not db:
            db = env.get_db_cnx()

        try:
          ev = cls(env, event, None, db)
        except:
          env.log.error("Could not run the event %s" % (event,))
          return
        #ev.lastrun = 1
        now = int(time.time())

        cursor = db.cursor()
        cursor.execute("SELECT name FROM client ORDER BY name")
        for client, in cursor:
          env.log.info("Running event for client: %s" % (client, ))
          clev = cls(env, event, client)
          clev.trigger(req, client, ev.lastrun, now)
        ev.lastrun = now
        ev.update()
    triggerall = classmethod(triggerall)
