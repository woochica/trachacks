from trac.core import *
from trac.env import IEnvironmentSetupParticipant
import trac.ticket.notification as note


def get_recipients(self, tktid):
  self.env.log.debug('NeverNotifyUpdaterPlugin: active, getting recipients for %s' % tktid)
  notify_reporter = self.config.getbool('notification',
					'always_notify_reporter')
  notify_owner = self.config.getbool('notification',
				     'always_notify_owner')
  notify_updater = self.config.getbool('notification', 
				       'always_notify_updater')

  ccrecipients = self.prev_cc
  torecipients = []
  cursor = self.db.cursor()
  
  # Harvest email addresses from the cc, reporter, and owner fields
  cursor.execute("SELECT cc,reporter,owner FROM ticket WHERE id=%s",
		 (tktid,))
  row = cursor.fetchone()
  def preplist (lst):
    return lst and lst.replace(',',' ').split() or []
  if row:
      ccrecipients += preplist(row[0])
      self.reporter = row[1]
      self.owner = row[2]
      if notify_reporter:
        torecipients += preplist(row[1])
      if notify_owner:
        torecipients += preplist(row[2])

  # Harvest email addresses from the author field of ticket_change(s)
  if notify_updater:
      cursor.execute("SELECT DISTINCT author,ticket FROM ticket_change "
         "WHERE ticket=%s", (tktid,))
      for author,ticket in cursor:
	torecipients.append(author)

  # Suppress the updater from the recipients
  updater = None
  cursor.execute("SELECT author FROM ticket_change WHERE ticket=%s "
		 "ORDER BY time DESC LIMIT 1", (tktid,))
  for updater, in cursor:
      break
  else:
    cursor.execute("SELECT reporter FROM ticket WHERE id=%s",
		   (tktid,))
    for updater, in cursor:
      break

  def finder(r):
    rtn = r and (((r.find('@') and updater.find(r))
                  or updater == r
                  or updater.find(r+'@'+defaultDomain)) >= 0)
    self.env.log.debug('NeverNotifyUpdaterPlugin: testing recipient %s to see if they are the updater %s, %s' % (r, updater, rtn))
    if rtn:
      self.env.log.debug('NeverNotifyUpdaterPlugin: blocking recipient %s' % r)
      return rtn

  torecipients = [r for r in torecipients if not finder(r)]
  ccrecipients = [r for r in ccrecipients if not finder(r)]
  self.env.log.debug('NeverNotifyUpdaterPlugin: tos , ccs = %s, %s' % (torecipients, ccrecipients))
  return (torecipients, ccrecipients)

class NeverNotifyUpdaterSetupParticipant(Component):
    """ This component monkey patches note.TicketNotifyEmail.get_recipients so that track will never 
    notify the person who updated the ticket about their own update"""
    implements(IEnvironmentSetupParticipant)
    def __init__(self):
      #only if we should be enabled do we monkey patch
      if self.compmgr.enabled[self.__class__]:
        note.TicketNotifyEmail.get_recipients = get_recipients



