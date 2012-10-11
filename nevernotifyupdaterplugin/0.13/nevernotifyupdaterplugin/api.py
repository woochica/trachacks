from trac.core import *
import re
from trac.env import IEnvironmentSetupParticipant
import trac.ticket.notification as note

from __future__ import with_statement


class NeverNotifyUpdaterSetupParticipant(Component):
    """ This component monkey patches note.TicketNotifyEmail.get_recipients so that trac will never 
    notify the person who updated the ticket about their own update"""
    implements(IEnvironmentSetupParticipant)
    def __init__(self):
      #only if we should be enabled do we monkey patch


      old_get_recipients = note.TicketNotifyEmail.get_recipients
      def is_enabled():
        return self.compmgr.enabled[self.__class__]

      def new_get_recipients(self, tktid):
        self.env.log.debug('NeverNotifyUpdaterPlugin: getting recipients for %s' % tktid)
        (torecipients, ccrecipients) = old_get_recipients(self,tktid)
        if not is_enabled():
          self.env.log.debug('NeverNotifyUpdaterPlugin: disabled, returning original results')
          return (torecipients, ccrecipients)

        self.env.log.debug('NeverNotifyUpdaterPlugin: START tkt:%s, tos , ccs = %s, %s' %
                           (tktid, torecipients, ccrecipients))
        defaultDomain = self.env.config.get("notification", "smtp_default_domain")
        domain = ''
        if defaultDomain: domain = '@'+defaultDomain

        updater = None
        up_em = None
        with self.env.db_query as db:
            cursor = db.cursor()
            # Suppress the updater from the recipients
            cursor.execute("SELECT author FROM ticket_change WHERE ticket=%s "
                           "ORDER BY time DESC LIMIT 1", (tktid,))
            for updater, in cursor: break
            else:
              cursor.execute("SELECT reporter FROM ticket WHERE id=%s",
                             (tktid,))
              for updater, in cursor: break

            cursor.execute("SELECT value FROM session_attribute WHERE name='email' and sid=%s;",(updater,))
            for up_em, in cursor: break

        def finder(r):
          if not r:
            return None
          self.env.log.debug('NeverNotifyUpdaterPlugin: testing recipient %s' \
                               ' to see if they are the updater %s'\
                               % ([r, r+domain], [updater, up_em, updater+domain]))
          regexp = "<\s*%s(%s)?\s*>" % (r, domain);
          rtn = (updater == r 
                 or updater == r+domain 
                 or updater+domain == r 
                 or updater+domain == r+domain
                 # user prefs email
                 or up_em == r 
                 or up_em == r+domain
                 # handles names followed by emails
                 or re.findall(regexp, updater)
                 or re.findall(regexp, updater+domain))
          if rtn:
            self.env.log.debug('NeverNotifyUpdaterPlugin: blocking recipient %s' % r)
            return rtn

        torecipients = [r for r in torecipients if not finder(r)]
        ccrecipients = [r for r in ccrecipients if not finder(r)]
        self.env.log.debug('NeverNotifyUpdaterPlugin: DONE tos , ccs = %s, %s' %
                           (torecipients, ccrecipients))
        return (torecipients, ccrecipients)


      if self.compmgr.enabled[self.__class__]:
        note.TicketNotifyEmail.get_recipients = new_get_recipients

    def environment_created(self):
      pass

    def environment_needs_upgrade(self, db):
      pass

    def upgrade_environment(self, db):
      pass




