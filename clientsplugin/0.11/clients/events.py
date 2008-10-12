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

    def __init__(self, env, name=None, db=None):
        self.env = env
        if name:
            name = simplify_whitespace(name)
        if name:
            if not db:
                db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute("SELECT summary, action, lastrun "
                           "FROM client_events "
                           "WHERE name=%s", (name,))
            row = cursor.fetchone()
            if not row:
                raise TracError('Client Event %s does not exist.' % name)
            self.name = self._old_name = name
            self.summary = row[0] or ''
            self.action = row[1] or ''
            self.lastrun = row[2] or 0
            self.loadoptions(db)
        else:
            self.name = self._old_name = None
            self.summary = ''
            self.action = ''
            self.lastrun = 0


    def loadoptions(self, db):
        assert self.exists, 'Cannot load options for a non-existent client event'
        system = ClientEventsSystem(self.env);
        summary = system.get_summary(self.summary)
        assert summary is not None, 'Invalid summary %s for client event' % self.summary
        action = system.get_action(self.action)
        assert action is not None, 'Invalid action %s for client event' % self.action

        options = {}
        cursor = db.cursor()
        cursor.execute("SELECT name, value "
                       "FROM client_event_summary_options "
                       "WHERE client_event=%s AND client=''", (self._old_name,))
        for name, value in cursor:
          options[name] = value
        self.summary_options = {}
        for option in summary.instance_options():
          option['md5'] = md5.new(option['name']).hexdigest()
          if options.has_key(option['name']):
            option['value'] = options[option['name']]
          self.summary_options[option['name']] = option

        options = {}
        cursor = db.cursor()
        cursor.execute("SELECT name, value "
                       "FROM client_event_action_options "
                       "WHERE client_event=%s AND client=''", (self._old_name,))
        for name, value in cursor:
          options[name] = value
        self.action_options = {}
        for option in action.instance_options():
          option['md5'] = md5.new(option['name']).hexdigest()
          if options.has_key(option['name']):
            option['value'] = options[option['name']]
          else:
            option['value'] = ''
          self.action_options[option['name']] = option

    exists = property(fget=lambda self: self._old_name is not None)


    def delete(self, db=None):
        assert self.exists, 'Cannot deleting non-existent client event'
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()
        self.env.log.info('Deleting client event %s' % self.name)
        cursor.execute("DELETE FROM client_events WHERE name=%s", (self.name,))

        self.name = self._old_name = None

        if handle_ta:
            db.commit()

    def insert(self, db=None):
        assert not self.exists, 'Cannot insert existing client event'
        system = ClientEventsSystem(self.env);
        assert system.get_summary(self.summary) is not None , 'Invalid summary'
        assert system.get_action(self.action) is not None, 'Invalid action'
        self.name = simplify_whitespace(self.name)
        assert self.name, 'Cannot create client event with no name'
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        # Todo: verify client_event with that name does not currently exist...
        cursor = db.cursor()
        self.env.log.debug("Creating new client event '%s'" % self.name)
        cursor.execute("INSERT INTO client_events (name,summary,action,lastrun) "
                       "VALUES (%s,%s,%s,%s)",
                       (self.name, self.summary, self.action, int(time.time())))

        if handle_ta:
            db.commit()

    def update_client_options(self, client, opttype, options, db=None):
        assert self.exists, 'Cannot update non-existent client event'
        assert opttype in ('summary', 'action'), 'Invalid options type'
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        table = 'client_event_' + opttype + '_options'
        cursor = db.cursor()
        self.env.log.info('Updating client event "%s"' % self._old_name)
        cursor.execute("DELETE FROM " + table + " "
                       "WHERE client_event=%s AND client=%s",
                       (self._old_name, client))
        for option in options.values():
          cursor.execute("INSERT INTO " + table + " (client_event, client, name, value) "
                         "VALUES (%s, %s, %s, %s)",
                         (self._old_name, client, option['name'], option['value']))

        if handle_ta:
            db.commit()


    def update_options(self, db=None):
        assert self.exists, 'Cannot update non-existent client event'
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        self.update_client_options('', 'summary', self.summary_options, db)
        self.update_client_options('', 'action', self.action_options, db)

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
        self.env.log.info('Updating client event "%s"' % self.name)
        cursor.execute("UPDATE client_events SET lastrun=%s "
                       "WHERE name=%s",
                       (int(self.lastrun), self._old_name))

        if handle_ta:
            db.commit()

    def select(cls, env, db=None):
        if not db:
            db = env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT name, summary, action, lastrun "
                       "FROM client_events "
                       "ORDER BY name")
        for name, summary, action, lastrun in cursor:
            client = cls(env)
            client.name = client._old_name = name
            client.summary = summary or ''
            client.action = action or ''
            client.lastrun = lastrun or 0
            client.loadoptions(db)
            yield client
    select = classmethod(select)
