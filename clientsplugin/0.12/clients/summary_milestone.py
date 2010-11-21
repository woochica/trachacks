# -*- coding: utf-8 -*-
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


class ClientMilestoneSummary(Component):
  implements(IClientSummaryProvider)

  client = None
  debug = False

  def get_name(self):
    return "Milestone Summary"

  def get_description(self):
    return "Provide a summary of all tickets within milestones that have completion dates set where at least one ticket for that client is not closed in that milestone"

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
    def myformat_hours(hrs, fallback='No estimate available'):
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
      return fallback

    client = self.client
    xml = etree.Element('clientsplugin')

    # Place basic client info here
    xclient = etree.SubElement(xml, 'client')
    etree.SubElement(xclient, 'name').text = client
    if fromdate:
      etree.SubElement(xclient, 'lastupdate').text = myformat_date(fromdate)

    # Information about milestones
    milestones = {}
    xmilestones = etree.SubElement(xml, 'milestones')

    db = self.env.get_read_db()
    have_data = False
    # Load in a summary of the client's tickets
    sql = ("""\
      SELECT t.id, t.summary, t.description, t.status, t.milestone,
        m.due, m.completed, m.description AS mdesc,
        tcust2.value AS estimatedhours, tcust3.value AS totalhours
      FROM ticket_custom AS tcust
      INNER JOIN ticket AS t ON tcust.ticket=t.id
      LEFT JOIN ticket_custom AS tcust2 ON t.id=tcust2.ticket AND tcust2.name='estimatedhours'
      LEFT JOIN ticket_custom AS tcust3 ON t.id=tcust3.ticket AND tcust3.name='totalhours'
      LEFT JOIN milestone m ON t.milestone=m.name
      WHERE tcust.name = 'client'
        AND tcust.value = %s
        AND t.milestone IN (
          SELECT DISTINCT st.milestone
          FROM ticket_custom AS stcust
          INNER JOIN ticket AS st ON stcust.ticket=st.id
          INNER JOIN milestone AS sm ON st.milestone=sm.name
          WHERE stcust.name = tcust.name
          AND stcust.value = tcust.value
          AND (sm.due > %s OR sm.completed > %s))
      ORDER BY m.due ASC
      """)
    cur2 = db.cursor()
    now = int(time.time()*1000000)
    cur2.execute(sql, (client, now, (now - (7*24*60*60*1000000))))
    xsummary = etree.SubElement(xml, 'summary')
    for tid, summary, description, status, milestone, due, completed, mdescription, estimatedhours, totalhours in cur2:
      have_data = True
      if milestone:
        if not milestones.has_key(milestone):
          xmilestone = etree.SubElement(xmilestones, 'milestone')
          etree.SubElement(xmilestone, 'name').text = milestone
          etree.SubElement(xmilestone, 'duetimestamp').text = str(due)
          etree.SubElement(xmilestone, 'due').text = myformat_date(due)
          if completed:
            etree.SubElement(xmilestone, 'completed').text = myformat_date(completed)
          if mdescription:
            xmilestone.append(etree.XML('<description>%s</description>' % wiki_to_html(extract_client_text(mdescription), self.env, req)))
          else:
            etree.SubElement(xmilestone, 'description').text = ''
          # Store for use
          milestones[milestone] = { 'hours': 0, 'xml': xmilestone }

        # Add hours to create a total.
        if estimatedhours:
          milestones[milestone]['hours'] += float(estimatedhours) 

      self.env.log.debug("  Summarising ticket #%s" % tid)
      ticket = etree.SubElement(xsummary, 'ticket')
      etree.SubElement(ticket, 'id').text = str(tid)
      etree.SubElement(ticket, 'summary').text = summary
      ticket.append(etree.XML('<description>%s</description>' % wiki_to_html(extract_client_text(description), self.env, req)))
      etree.SubElement(ticket, 'status').text = status
      etree.SubElement(ticket, 'milestone').text = milestone
      # For conveneince, put the date here too (keeps the XSLTs simpler)
      etree.SubElement(ticket, 'due').text = myformat_date(due)
      if estimatedhours:
        etree.SubElement(ticket, 'estimatedhours').text = myformat_hours(estimatedhours)

      if totalhours:
        etree.SubElement(ticket, 'totalhours').text = myformat_hours(totalhours, 'None')


    # Put the total hours into the milestone info
    for milestone in milestones:
      etree.SubElement(milestones[milestone]['xml'], 'estimatedhours').text = myformat_hours(milestones[milestone]['hours'])

    if self.debug:
      file = open('/tmp/send-client-email.xml', 'w')
      file.write(etree.tostring(xml, pretty_print=True))
      file.close()
      self.env.log.debug(" Wrote XML to /tmp/send-client-email.xml")

    if not have_data:
      return None

    return xml
