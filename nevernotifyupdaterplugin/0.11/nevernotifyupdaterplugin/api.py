import trac.ticket.notification as note


def get_recipients(self, tktid):
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
  if row:
      ccrecipients += row[0] and row[0].replace(',', ' ').split() or []
      self.reporter = row[1]
      self.owner = row[2]
      if notify_reporter:
	torecipients.append(row[1])
      if notify_owner:
	torecipients.append(row[2])

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

  if not notify_updater:
    filter_out = True
#       if notify_reporter and (updater == self.reporter):
#     filter_out = False
#       if notify_owner and (updater == self.owner):
#     filter_out = False
    if filter_out:
      torecipients = [r for r in torecipients if r and r != updater]
      ccrecipients = [r for r in ccrecipients if r and r != updater]
  elif updater:
    torecipients.append(updater)

  return (torecipients, ccrecipients)

note.TicketNotifyEmail.get_recipients = get_recipients
