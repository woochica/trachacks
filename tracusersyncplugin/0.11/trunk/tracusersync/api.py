import os
import fileinput
from trac.core import *
from trac.config import *
from trac.env import Environment

class UserSyncAdmin(Component):
  def get_envs(self, parentdir):
     """Return array of available Trac environments
     @param parentdir : the TRAC_ENV_PARENT_DIR to look in
     """
     tracenvs = []
     for dirname in os.listdir(parentdir):
        dirnam = os.path.join(parentdir,dirname)
        if os.path.exists( os.path.join(dirnam,os.path.join('conf','trac.ini')) ):
           tracenvs.append( dirname )
     self.env.log.debug('Found trac envs: %s' % (', '.join(tracenvs)))
     return tracenvs

  def get_pwd_users(self, pwdfile):
     """Return array of usernames from the password file
     @param pwdfile : Name of the password file
     """
     users = []
     try:
        for line in fileinput.input(pwdfile):
           rec = line.split(':')
           user = rec.pop(0)
           if user:
              users.append(user)
     except IOError:
        self.env.log.debug('empty user record in _get_users')
     return users

  def get_perm_groups(self,path):
     """Get array of permission groups (e.g. anonymous,authenticated) defined in the given environment.
     These 'users' should e.g. never be purged on cleanup
     """
     users = []
     env = Environment(path)
     sids = []
     self.env.log.debug('Get users to keep from environment path %s' % (path,))
     db = env.get_db_cnx()
     cursor = db.cursor()
     cursor.execute('SELECT DISTINCT username FROM permission WHERE username NOT IN (SELECT DISTINCT sid FROM session_attribute UNION SELECT DISTINCT sid FROM session UNION SELECT DISTINCT name FROM auth_cookie)')
     for row in cursor: users.append(row[0])
     self.env.log.debug('Permission groups for %s: %s' % (path,','.join(users)))
     for user in env.config.getlist('user_sync','users_keep'):
       if not user in users: users.append(user)
     return users

  def get_tracenv_users(self, path, userlist=''):
     """Get array of users defined in the specified environment having data assigned
     @param path path to the environment
     @param userlist comma separated list of users to restrict the result to (e.g. the users from the password file), each user enclosed in single quotes (for SQL)
     """
     env = Environment(path)
     sids = []
     self.env.log.debug('Get users from %s' % (path,))
     db = env.get_db_cnx()
     cursor = db.cursor()
     if userlist:
       cursor.execute("SELECT DISTINCT sid FROM session_attribute WHERE sid IN (%s) AND name != 'enabled'" % (userlist,))
     else:
       cursor.execute("SELECT DISTINCT sid FROM session_attribute WHERE name != 'enabled'")
     for row in cursor:
        sids.append(row[0])
     return sids

  def get_tracenv_userdata(self, path, userlist=''):
     self.env.log.debug('Get user data from %s' % (path,))
     env = Environment(path)
     db = env.get_db_cnx()
     cursor = db.cursor()
     data = {}
     sync_fields = self.env.config.getlist('user_sync','sync_fields')
     attr = "'"+"','".join(sync_fields)+"','email_verification_sent_to','email_verification_token'"
     self.env.log.debug('* Checking attributes: %s' % (attr,))
     if userlist:
       cursor.execute("SELECT sid,name,value FROM session_attribute WHERE sid IN (%s) AND name IN (%s)" % (userlist,attr,))
     else:
       cursor.execute("SELECT sid,name,value FROM session_attribute WHERE name IN (%s)" % (attr,))
     for row in cursor:
       if not row[0] in data: data[row[0]] = {}
       data[row[0]][row[1]] = row[2]
     for sid in data.iterkeys():
        no_data = True
        for att in sync_fields:
           if att in data[sid]:
              no_data = False
              break
        if no_data:
              self.env.log.debug('No data for %s in %s' % (sid,path,))
              data[sid] = Null
              continue
        data[sid]['path'] = path
        cursor.execute("SELECT authenticated FROM session_attribute WHERE sid='%s'" % (sid,))
        for row in cursor: data[sid]['authenticated'] = row[0]
        cursor.execute("SELECT datetime(last_visit,'unixepoch') AS last_visit FROM session WHERE sid='%s'" % (sid,))
        for row in cursor: data[sid]['last_visit'] = row[0]
     return data

  def merge(self,coll):
    """Merge all user records so the result contains exactly one record per
    user with all sync_fields updated
    @param coll : collection of user data
    @return res : resulting collection of updated records
    @return err : list of conflicting records (only the newest record per user)
    """
    res = {}
    err = []
    merge_conflicts = self.env.config.get('user_sync','merge_conflicts')
    self.env.log.debug('Syncing fields %s' % (self.env.config.get('user_sync','sync_fields')))
    self.env.log.debug('Merge conflicts set to %s' % (merge_conflicts))
    for sid in coll.iterkeys():
      res[sid] = coll[sid].pop()
      for rec in coll[sid]:
         for att in self.env.config.getlist('user_sync','sync_fields'):
            if not att in rec: continue
            if not att in res[sid]:
              res[sid][att] = rec[att]
              continue
            if res[sid][att] == rec[att]: continue
            if merge_conflicts.lower() == 'newer':
               if rec['last_visited'] > res[sid]['last_visited']:
                  self.env.log.debug('Replaced record: "%s" = "%s"' % (att,rec[sid][att],rec[att]))
                  res[sid][att] = rec[att]
               else:
                  self.env.log.debug('Skipped conflicting record: "%s" = "%s"' % (att,rec[sid][att],rec[att]))
                  err.append(rec)
                  res[sid] = Null
            else:
               err.append(rec)
               del res[sid]
         if sid in res and 'email' in self.env.config.getlist('user_sync','sync_fields') and 'email_verification_sent_to' in rec and not 'email_verification_token' in rec:
            res[sid]['email_verification_sent_to'] = rec['email_verification_sent_to']
    return res, err

  def update_tracenv_userdata(self, path, userdata):
    """Update the userdata in the specified environment using the records passed
    by userdata.
    @param path     : path to the trac environment to update
    @param userdata : collection of userdata as returned from merge()
    @return success : boolean
    @return msg     : details
    """
    sql = []
    exists = ''
    msg = ''
    envpath, tracenv = os.path.split(path)
    self.env.log.debug('Updating userdata in environment %s' % (path,))
    dryrun = self.env.config.getbool('user_sync','dryrun',True)
    if not dryrun:
      self.env.log.debug('HOT!!! We are NOT in dryrun mode!')
    else: self.env.log.debug('TESTING - we ARE in dryrun mode.')
    try:
      env = Environment(path)
    except IOError:
      self.env.log.debug('Could not initialize environment at %s' % (path,))
      return False, 'Could not initialize environment at %s' % (path,)
    db = env.get_db_cnx()
    cursor = db.cursor()
    if not dryrun: self.env.log.debug('Updating database for %s' % (tracenv,))
    for user in userdata:
      authenticated = userdata[user]['authenticated'] or 0
      for att in userdata[user]:
        if att in ['path','authenticated','last_visit']: continue
        cursor.execute("SELECT value FROM session_attribute WHERE sid='%s' AND name='%s' AND authenticated=%s" % (user,att,authenticated,))
        for row in cursor: exists = row[0]
        if exists:
          if exists == userdata[user][att]: continue
          if not dryrun: cursor.execute("UPDATE session_attribute SET value='%s' WHERE sid='%s' AND name='%s' AND authenticated=%s;\n" % (userdata[user][att],user,att,authenticated,))
          sql.append("UPDATE session_attribute SET value='%s' WHERE sid='%s' AND name='%s' AND authenticated=%s;\n" % (userdata[user][att],user,att,authenticated,))
        else:
          if not dryrun: cursor.execute("INSERT INTO session_attribute (sid,authenticated,name,value) VALUES('%s',%s,'%s','%s');\n" % (user,authenticated,att,userdata[user][att]))
          sql.append("INSERT INTO session_attribute (sid,authenticated,name,att) VALUES('%s',%s,'%s','%s');\n" % (user,authenticated,att,userdata[user][att]))
    if len(sql):
      if not dryrun: db.commit()
      sql_file_path = self.env.config.get('user_sync','sql_file_path') or os.path.join(self.env.path,'log')
      if sql_file_path.lower() == 'none':
        self.env.log.debug('SQLFile disabled (sql_file_path is "none")')
      else:
        sqlfile = '%s.sql' % (tracenv,)
        sqlfile = os.path.join(sql_file_path,sqlfile)
        try:
          if os.path.exists(sqlfile): os.unlink(sqlfile)
          self.env.log.debug('Writing SQL to %s' % (sqlfile,))
          f = open(sqlfile,'a')
          f.write('--- SQL for Trac environment %s\n' % (tracenv,));
          f.writelines(sql)
          f.close()
        except IOError:
          self.env.log.debug('Could not write SQL file %s!' % (sqlfile,))
          return False, 'Could not write SQL file %s!' % (sqlfile,)
        except ValueError:
          self.env.log.debug('No value for sqlfile?')
        if dryrun: msg = 'Wrote SQL for Trac environment %s to %s' % (tracenv,sqlfile,)
        else: msg = 'Updated userdata in environment %s. SQL was additionally written to %s' % (tracenv,sqlfile,)
    else:
      msg = 'No updates for Trac environment %s' % (tracenv)
    self.env.log.debug('Done updating userdata in environment %s' % (path,))
    return True, msg

  def do_purge(self):
    """Purge obsolete data - i.e. environment data (sessions, preferences,
    permissions) from users no longer existing
    """
    self.env.log.info('+ Purging obsolete data')
    return True, 'The purging functionality is not yet implemented.'
