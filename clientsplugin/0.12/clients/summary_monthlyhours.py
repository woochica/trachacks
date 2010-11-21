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


class ClientMonthlyHoursSummary(Component):
  implements(IClientSummaryProvider)

  client = None
  debug = False

  def get_name(self):
    return "Monthly Hours Summary"

  def get_description(self):
    return "Details the total hours spent on tickets for the last three months."

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
    months = {}
    xmonths = etree.SubElement(xml, 'months')

    db = self.env.get_read_db()
    have_data = False
    # Load in a summary of the client's tickets
    sql = ("""\
      SELECT t.id, t.summary, t.description, t.status,
        SUM(tchng.newvalue) AS totalhours, CONCAT(MONTHNAME(FROM_UNIXTIME(tchng.time/1000000)), " ", YEAR(FROM_UNIXTIME(tchng.time/1000000))) AS month
      FROM ticket_custom AS tcust
      INNER JOIN ticket AS t ON tcust.ticket=t.id
      INNER JOIN ticket_change AS tchng ON t.id=tchng.ticket AND tchng.field='hours' AND tchng.oldvalue=0
      WHERE tcust.name = 'client'
        AND tcust.value = %s
        AND tchng.time >= (UNIX_TIMESTAMP(PERIOD_ADD(EXTRACT(YEAR_MONTH FROM NOW()), -3)*100+1)*1000000)
      GROUP BY t.id, MONTH(FROM_UNIXTIME(tchng.time/1000000))
      ORDER BY tchng.time desc;
      """)
    cur2 = db.cursor()
    cur2.execute(sql, (client,))
    xsummary = etree.SubElement(xml, 'summary')
    for tid, summary, description, status, totalhours, month in cur2:
      have_data = True

      if not months.has_key(month):
        xmonth = etree.SubElement(xmonths, 'month')
        etree.SubElement(xmonth, 'name').text = month
        months[month] = { 'totalhours': 0, 'xml': xmonth }

      # Add hours to create a total.
      months[month]['totalhours'] += float(totalhours) 

      self.env.log.debug("  Summarising ticket #%s in %s" % (tid, month))
      ticket = etree.SubElement(xsummary, 'ticket')
      etree.SubElement(ticket, 'id').text = str(tid)
      etree.SubElement(ticket, 'summary').text = summary
      ticket.append(etree.XML('<description>%s</description>' % wiki_to_html(extract_client_text(description), self.env, req)))
      etree.SubElement(ticket, 'status').text = status
      etree.SubElement(ticket, 'month').text = month

      etree.SubElement(ticket, 'totalhours').text = myformat_hours(totalhours, 'None')


    # Put the total hours into the month info
    for month in months:
      etree.SubElement(months[month]['xml'], 'totalhours').text = myformat_hours(months[month]['totalhours'])

    if self.debug:
      file = open('/tmp/send-client-email.xml', 'w')
      file.write(etree.tostring(xml, pretty_print=True))
      file.close()
      self.env.log.debug(" Wrote XML to /tmp/send-client-email.xml")

    if not have_data:
      return None

    return xml
