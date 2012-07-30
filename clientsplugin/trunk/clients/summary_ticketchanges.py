import re
import os
import sys
import locale
import time
import codecs
from datetime import datetime
from optparse import OptionParser
from StringIO import StringIO

from trac.core import *
from trac.env import open_environment
from trac.util.datefmt import format_date, to_datetime
from trac.wiki import wiki_to_html
from genshi import escape

from lxml import etree
from clients.summary import IClientSummaryProvider
from clients.processor import extract_client_text


class ClientTicketChanges(Component):
  implements(IClientSummaryProvider)

  client = None
  debug = False

  def get_name(self):
    return "Ticket Change Summary"

  def get_description(self):
    return "Provide a summary of ticket changes since the last run"

  def options(self, client=None):
    return []

  def init(self, event, client):
    self.client = client
    return True

  def get_summary(self, req, fromdate = None, todate = None):
    def myformat_date(dte):
      if dte:
        return format_date(dte, '%e %b %Y')
      return 'No date set'
    def myformat_hours(hrs):
      from math import floor
      if hrs:
        hrs = float(hrs)
        if 0 != hrs:
          neg = False
          if hrs < 0:
            neg = True
            hours *= -1
          mins = floor((hrs - floor(hrs)) * 60)
          str = ''
          if neg:
            str = '-'
          if hrs:
            str = "%s%sh" % (str, int(floor(hrs)))
          if mins:
            str = "%s %sm" % (str, int(mins))
          return str;
      return 'No estimate available'

    client = self.client
    xml = etree.Element('clientsplugin')

    # Place basic client info here
    xclient = etree.SubElement(xml, 'client')
    etree.SubElement(xclient, 'name').text = client
    if fromdate:
      etree.SubElement(xclient, 'lastupdate').text = myformat_date(fromdate)

    db = self.env.get_read_db()
    have_data = False
    # Load in any changes that have happend
    sql = ("""\
      SELECT t.id, t.summary, t.description, t.status, t.resolution, t.milestone, m.due,
        tchng.field, tchng.oldvalue, tchng.newvalue
      FROM ticket_custom tcust
      INNER JOIN ticket AS t ON tcust.ticket=t.id
      INNER JOIN ticket_change AS tchng ON t.id=tchng.ticket
      LEFT JOIN milestone AS m ON t.milestone=m.name
      WHERE tcust.name = 'client'
        AND tcust.value = %s
        AND tchng.field IN ('comment', 'status', 'resolution', 'milestone')
        AND tchng.time >= %s
        AND tchng.time < %s
        AND t.milestone IN (
          SELECT DISTINCT st.milestone
          FROM ticket_custom AS stcust
          INNER JOIN ticket AS st ON stcust.ticket=st.id
          INNER JOIN milestone AS sm ON st.milestone=sm.name
          WHERE stcust.name = tcust.name
          AND stcust.value = tcust.value
          AND sm.due > 0)
      ORDER BY t.time
      """)
    cur2 = db.cursor()
    cur2.execute(sql, (client, fromdate*1000000, todate*1000000))
    changes = etree.SubElement(xml, 'changes')
    lasttid = 0
    for tid, summary, description, status, resolution, milestone, due, cgfield, oldvalue, newvalue in cur2:
      text = ''
      if 'status' == cgfield:
        text = 'Status changed from "%s" to "%s"' % (oldvalue, newvalue)
      elif 'milestone' == cgfield:
        text = 'Milestone changed from "%s" to "%s" - please check for revised delivery date.' % (oldvalue, newvalue)
      elif 'resolution' == cgfield:
        if oldvalue and not newvalue:
          text = 'Resolution removed'
        elif not oldvalue and newvalue:
          text = 'Resolution set to "%s"' % (newvalue)
        else:
          text = 'Resolution changed from "%s" to "%s"' % (oldvalue, newvalue)
      elif 'comment' == cgfield:
        # Todo - extract...
        text = extract_client_text(newvalue).strip()
        if '' == text:
          # No comments for the client here so ignore it.
          continue
        text = "''Comment for your information:''[[BR]][[BR]]" + text
      else:
        # Client should not know any more than this
        continue
      
      if self.debug:
        self.env.log.debug("  Change notification (%s) for ticket #%s" % (cgfield, tid))
      have_data = True
      if lasttid != tid:
        ticket = etree.SubElement(changes, 'ticket')
        etree.SubElement(ticket, 'id').text = str(tid)
        etree.SubElement(ticket, 'summary').text = summary
        ticket.append(etree.XML('<description>%s</description>' % wiki_to_html(extract_client_text(description), self.env, req)))
        etree.SubElement(ticket, 'status').text = status
        etree.SubElement(ticket, 'resolution').text = resolution
        etree.SubElement(ticket, 'milestone').text = milestone
        etree.SubElement(ticket, 'due').text = myformat_date(due)
        changelog = etree.SubElement(ticket, 'changelog')

      detail = etree.XML('<detail>%s</detail>' % wiki_to_html(text, self.env, req))
      detail.set('field', cgfield)
      if oldvalue:
        detail.set('oldvalue', oldvalue)
      if newvalue:
        detail.set('newvalue', newvalue)
      changelog.append(detail)
      lasttid = tid

    if self.debug:
      file = open('/tmp/send-client-email.xml', 'w')
      file.write(etree.tostring(xml, pretty_print=True))
      file.close()
      self.env.log.debug(" Wrote XML to /tmp/send-client-email.xml")

    if not have_data:
      return None

    return xml
