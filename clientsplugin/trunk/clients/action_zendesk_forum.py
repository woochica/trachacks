import re
import os
import sys
import locale
import time
import codecs
import httplib
import urlparse
from datetime import datetime
from StringIO import StringIO

from trac.core import *
from trac.env import open_environment
from trac.util.datefmt import format_date, to_datetime
from trac.wiki import wiki_to_html
from genshi import escape

from lxml import etree
from clients.action import IClientActionProvider


class ClientActionZendesk(Component):
  implements(IClientActionProvider)

  client = None
  debug = False

  def get_name(self):
    return "Post to Zendesk"

  def get_description(self):
    return "Post the summary to a Zendesk forum topic"

  def options(self, client=None):
    if client is None:
      yield {'name': 'XSLT', 'description': 'Formatting XSLT to convert the summary to a Zendesk compatible post', 'type': 'large'}
      yield {'name': 'Username', 'description': 'Zendesk username', 'type': 'medium'}
      yield {'name': 'Password', 'description': 'Zendesk password', 'type': 'medium'}
      yield {'name': 'Method', 'description': 'Interaction Method', 'type': 'list', 'vals': ['POST', 'PUT']}
    else:
      yield {'name': 'Zendesk URI', 'description': 'Zendesk Forum REST URI', 'type': 'medium'}


  def init(self, event, client):
    self.client = client
    if not event.action_options.has_key('XSLT') or not event.action_options['XSLT']['value']:
      return False
    try:
      self.transform = etree.XSLT(etree.fromstring(str(event.action_options['XSLT']['value'])))
    except:
      print "Error: Cannot load/parse stylesheet"
      return False

    if not event.action_options.has_key('Username') or not event.action_options['Username']['value']:
      return False
    self.username = event.action_options['Username']['value']

    if not event.action_options.has_key('Password') or not event.action_options['Password']['value']:
      return False
    self.password = event.action_options['Password']['value']

    if not event.action_options.has_key('Method') or not event.action_options['Method']['value']:
      return False
    self.method = event.action_options['Method']['value']

    if not event.action_client_options.has_key('Zendesk URI') or not event.action_client_options['Zendesk URI']['value']:
      return False
    self.uri = event.action_client_options['Zendesk URI']['value']

    return True


  def perform(self, req, summary):
    def parseuri(uri): 
      """Parse URI, return (host, port, path) tuple.

      >>> parseuri('http://example.org/testing?somequery#frag')
      ('example.org', 80, '/testing?somequery')
      >>> parseuri('http://example.net:8080/test.html')
      ('example.net', 8080, '/test.html')
      """

      scheme, netplace, path, query, fragid = urlparse.urlsplit(uri)

      if ':' in netplace: 
        host, port = netplace.split(':', 2)
        port = int(port)
      else: host, port = netplace, 80

      if query: path += '?' + query

      return host, port, path



    if summary is None:
      return False

    result = self.transform(summary)

    username = self.username
    password = self.password
    uri = self.uri

    host, port, path = parseuri(uri)

    okay = set([200, 201, 204])

    import base64
    userpass = username + ':' + password
    userpass = base64.encodestring(userpass).strip()
    authorization = 'Basic ' + userpass

    # Attempt to HTTP PUT the data
    h = httplib.HTTPConnection(host, port)

    data = str(result)
    h.putrequest('PUT', path)

    h.putheader('User-Agent', 'Trac/1.0')
    h.putheader('Accept', 'application/xml')
    h.putheader('Content-Type', 'text/xml')
    h.putheader('Authorization', authorization)
    h.putheader('Content-Length', len(data))
    h.endheaders()

    h.send(str(data))

    resp = h.getresponse()
    status = resp.status # an int

    # Got a response, now decide how to act upon it
    if status not in okay: 
      print 'Got "%s %s"' % (status, resp.reason)
      return False

    return True
