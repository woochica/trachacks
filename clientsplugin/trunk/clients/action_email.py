# -*- coding: utf-8 -*-
import re
import os
import sys
import locale
import time
import codecs
from datetime import datetime
from StringIO import StringIO

from trac import __version__
from trac.core import *
from trac.env import open_environment
from trac.util.datefmt import format_date, to_datetime
from trac.wiki import wiki_to_html
from genshi import escape

from lxml import etree
from clients.action import IClientActionProvider


class ClientActionEmail(Component):
  implements(IClientActionProvider)

  client = None
  debug = False

  def get_name(self):
    return "Send Email"

  def get_description(self):
    return "Send an email to a certain list of addresses"

  def options(self, client=None):
    if client is None:
      yield {'name': 'XSLT', 'description': 'Formatting XSLT to convert the summary to an email', 'type': 'large'}
      yield {'name': 'Subject', 'description': 'Email subject (use %s to replace the active client name)', 'type': 'medium'}
    else:
      yield {'name': 'Email Addresses', 'description': 'Comma separated list of email addresses', 'type': 'medium'}


  def init(self, event, client):
    self.client = client
    if not event.action_options.has_key('XSLT') or not event.action_options['XSLT']['value']:
      return False
    try:
      self.transform = etree.XSLT(etree.fromstring(str(event.action_options['XSLT']['value'])))
    except:
      self.env.log.error("Error: Cannot load/parse stylesheet")
      return False

    if not event.action_client_options.has_key('Email Addresses') or not event.action_client_options['Email Addresses']['value']:
      return False

    self.emails = []
    for email in event.action_client_options['Email Addresses']['value'].replace(',', ' ').split(' '):
      if '' != email.strip():
        self.emails.append(email.strip())

    if not self.emails:
      return False

    if not event.action_options.has_key('Subject') or not event.action_options['Subject']['value']:
      self.subject = 'Ticket Summary for %s'
    else:
      self.subject = event.action_options['Subject']['value']

    if self.subject.find('%s') >= 0:
      self.subject = self.subject % (client,)

    return True


  def perform(self, req, summary):
    if summary is None:
      return False
    self.config = self.env.config
    self.encoding = 'utf-8'
    subject = self.subject

    if not self.config.getbool('notification', 'smtp_enabled'):
      return False
    smtp_server = self.config['notification'].get('smtp_server')
    smtp_port = self.config['notification'].getint('smtp_port')
    from_email = self.config['notification'].get('smtp_from')
    from_name = self.config['notification'].get('smtp_from_name')
    replyto_email = self.config['notification'].get('smtp_replyto')
    from_email = from_email or replyto_email
    if not from_email:
      return False
    
    # Authentication info (optional)
    user_name = self.config['notification'].get('smtp_user')
    password = self.config['notification'].get('smtp_password')
    
    # Thanks to the author of this recipe:
    # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/473810
    
    from email.MIMEMultipart import MIMEMultipart
    from email.MIMEText import MIMEText
    from email.MIMEImage import MIMEImage
    from email.Charset import add_charset, SHORTEST
    add_charset( 'utf-8', SHORTEST, None, None )

    projname = self.config.get('project', 'name')
    
    # Create the root message and fill in the from, to, and subject headers
    msg_root = MIMEMultipart('alternative')
    msg_root['To'] = str(', ').join(self.emails)
    
    msg_root['X-Mailer'] = 'ClientsPlugin for Trac'
    msg_root['X-Trac-Version'] =  __version__
    msg_root['X-Trac-Project'] =  projname
    msg_root['Precedence'] = 'bulk'
    msg_root['Auto-Submitted'] = 'auto-generated'
    msg_root['Subject'] = subject
    msg_root['From'] = '%s <%s>' % (from_name or projname, from_email)
    msg_root['Reply-To'] = replyto_email
    msg_root.preamble = 'This is a multi-part message in MIME format.'
    
    view = 'plain'
    arg = "'%s'" % view
    result = self.transform(summary, view=arg)
    msg_text = MIMEText(str(result), view, self.encoding)
    msg_root.attach(msg_text)
    
    msg_related = MIMEMultipart('related')
    msg_root.attach(msg_related)
    
    view = 'html'
    arg = "'%s'" % view
    result = self.transform(summary, view=arg)
    #file = open('/tmp/send-client-email.html', 'w')
    #file.write(str(result))
    #file.close()

    msg_text = MIMEText(str(result), view, self.encoding)
    msg_related.attach(msg_text)
    
    # Handle image embedding...
    view = 'images'
    arg = "'%s'" % view
    result = self.transform(summary, view=arg)
    if result:
      images = result.getroot()
      if images is not None:
        for img in images:
          if 'img' != img.tag:
            continue
          if not img.get('id') or not img.get('src'):
            continue
          
          fp = open(img.get('src'), 'rb')
          if not fp:
            continue
          msg_img = MIMEImage(fp.read())
          fp.close()
          msg_img.add_header('Content-ID', '<%s>' % img.get('id'))
          msg_related.attach(msg_img)
    
    # Send the email
    import smtplib
    smtp = smtplib.SMTP() #smtp_server, smtp_port)
    if False and user_name:
        smtp.login(user_name, password)
    smtp.connect()
    smtp.sendmail(from_email, self.emails, msg_root.as_string())
    smtp.quit()
    return True
