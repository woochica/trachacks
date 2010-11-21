import md5
import sys
import time

from trac.core import *

from clients.summary import IClientSummaryProvider
from clients.action import IClientActionProvider



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

class ClientEvent(object):

    def __init__(self, env, name=None, client=None, db=None):
        self.env = env
        if name:
            name = simplify_whitespace(name)
        if name:
            db = self.env.get_read_db()
            cursor = db.cursor()
            cursor.execute("SELECT summary, action, lastrun "
                           "FROM client_events "
                           "WHERE name=%s", (name,))
            row = cursor.fetchone()
            if not row:
                raise TracError('Client Event %s does not exist.' % name)
            self.md5 = md5.new(name).hexdigest()
            self.name = self._old_name = name
            self.summary = row[0] or ''
            self.action = row[1] or ''
            self.lastrun = row[2] or 0
            self._load_options(client, db)
        else:
            self.name = self._old_name = None
            self.summary = ''
            self.action = ''
            self.lastrun = 0


    exists = property(fget=lambda self: self._old_name is not None)


    def delete(self, db=None):
        assert self.exists, 'Cannot deleting non-existent client event'

        @self.env.with_transaction(db)
        def do_delete(db):
            cursor = db.cursor()
            self.env.log.info('Deleting client event %s' % self.name)
            cursor.execute("DELETE FROM client_events WHERE name=%s", (self.name,))

            self.name = self._old_name = None

    def insert(self, db=None):
        assert not self.exists, 'Cannot insert existing client event'
        system = ClientEventsSystem(self.env);
        assert system.get_summary(self.summary) is not None , 'Invalid summary'
        assert system.get_action(self.action) is not None, 'Invalid action'
        self.name = simplify_whitespace(self.name)
        assert self.name, 'Cannot create client event with no name'

        @self.env.with_transaction(db)
        def do_insert(db):
            # Todo: verify client_event with that name does not currently exist...
            cursor = db.cursor()
            self.env.log.debug("Creating new client event '%s'" % self.name)
            cursor.execute("INSERT INTO client_events (name,summary,action,lastrun) "
                           "VALUES (%s,%s,%s,%s)",
                           (self.name, self.summary, self.action, int(time.time())))

    def _load_client_options(self, client, opttype, db):
        assert self.exists, 'Cannot update non-existent client event'
        assert opttype in ('summary', 'action'), 'Invalid options type'
        system = ClientEventsSystem(self.env);
        if 'summary' == opttype:
          thing = system.get_summary(self.summary)
          assert thing is not None , 'Invalid summary'
          self.summary_description = thing.get_description()
        else:
          thing = system.get_action(self.action)
          assert thing is not None, 'Invalid action'
          self.action_description = thing.get_description()

        options = {}
        table = 'client_event_' + opttype + '_options'
        cursor = db.cursor()
        cursor.execute("SELECT name, value "
                       "FROM " + table + " "
                       "WHERE client_event=%s AND client=%s",
                       (self._old_name, client or ''))
        for name, value in cursor:
          options[name] = value
        rv = {}
        for option in thing.options(client):
          option['md5'] = md5.new(option['name']).hexdigest()
          if options.has_key(option['name']):
            option['value'] = options[option['name']]
          else:
            option['value'] = ''
          rv[option['name']] = option
        return rv


    def _load_options(self, client, db):
        self.summary_options = self._load_client_options(None, 'summary', db)
        self.action_options = self._load_client_options(None, 'action', db)
        if client:
          self.summary_client_options = self._load_client_options(client, 'summary', db)
          self.action_client_options = self._load_client_options(client, 'action', db)


    def _update_client_options(self, client, opttype, options, db=None):
        assert self.exists, 'Cannot update non-existent client event'
        assert opttype in ('summary', 'action'), 'Invalid options type'
        system = ClientEventsSystem(self.env);
        if 'summary' == opttype:
          thing = system.get_summary(self.summary)
          assert thing is not None , 'Invalid summary'
        else:
          thing = system.get_action(self.action)
          assert thing is not None, 'Invalid action'

        @self.env.with_transaction(db)
        def do_update_client_options(db):
          table = 'client_event_' + opttype + '_options'
          cursor = db.cursor()
          self.env.log.info('Updating client event "%s"' % self._old_name)
          cursor.execute("DELETE FROM " + table + " "
                         "WHERE client_event=%s AND client=%s",
                         (self._old_name, client or ''))

          valid_options = []
          for option in thing.options(client):
            valid_options.append(option['name'])
          for option in options.values():
            if option['name'] in valid_options:
              cursor.execute("INSERT INTO " + table + " (client_event, client, name, value) "
                             "VALUES (%s, %s, %s, %s)",
                             (self._old_name, client or '', option['name'], option['value']))


    def update_options(self, client=None, db=None):
        assert self.exists, 'Cannot update non-existent client event'

        if client:
          self._update_client_options(client, 'summary', self.summary_client_options, db)
          self._update_client_options(client, 'action', self.action_client_options, db)
        else:
          self._update_client_options(None, 'summary', self.summary_options, db)
          self._update_client_options(None, 'action', self.action_options, db)


    def update(self, db=None):
        assert self.exists, 'Cannot update non-existent client event'
        self.name = simplify_whitespace(self.name)
        assert self.name, 'Cannot update client event with no name'

        @self.env.with_transaction(db)
        def do_update(db):
            cursor = db.cursor()
            self.env.log.info('Updating client event "%s"' % self._old_name)
            cursor.execute("UPDATE client_events SET lastrun=%s "
                           "WHERE name=%s",
                           (int(self.lastrun), self._old_name))

    def trigger(self, req, client, fromdate, todate, db=None):
        assert self.exists, 'Cannot trigger a client event that does not exits'
        system = ClientEventsSystem(self.env);
        summary = system.get_summary(self.summary)
        assert summary is not None , 'Invalid summary'
        action = system.get_action(self.action)
        assert action is not None, 'Invalid action'

        if not summary.init(self, client):
          self.env.log.info("Could not init summary")
          return False
        if not action.init(self, client):
          self.env.log.info("Could not init action")
          return False

        self.env.log.debug("Performing action")
        return action.perform(req, summary.get_summary(req, fromdate, todate))


    def select(cls, env, client=None, db=None):
        if not db:
            db = env.get_read_db()
        cursor = db.cursor()
        cursor.execute("SELECT name, summary, action, lastrun "
                       "FROM client_events "
                       "ORDER BY name")
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
        @env.with_transaction(db)
        def do_triggerall(db):
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
