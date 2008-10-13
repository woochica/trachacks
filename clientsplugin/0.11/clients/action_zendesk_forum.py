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

    redirect = set([301, 302, 307])
    authenticate = set([401])
    okay = set([200, 201, 204])

    authorized = False
    authorization = None
    tries = 0
    verbose = True

    while True: 
      # Attempt to HTTP PUT the data
      h = httplib.HTTPConnection(host, port)

      h.putrequest('PUT', path)

      h.putheader('User-Agent', 'Trac/1.0')
      h.putheader('Connection', 'keep-alive')
      h.putheader('Transfer-Encoding', 'chunked')
      h.putheader('Expect', '100-continue')
      h.putheader('Accept', 'application/xml')
      h.putheader('Content-Type', 'text/xml')
      h.putheader('Content-Length', len(str(result)))
      if authorization: 
         h.putheader('Authorization', authorization)
      h.endheaders()

      # Chunked transfer encoding
      # Cf. 'All HTTP/1.1 applications MUST be able to receive and 
      # decode the "chunked" transfer-coding'
      # - http://www.w3.org/Protocols/rfc2616/rfc2616-sec3.html
      while True: 
         #bytes = f.read(2048)
         bytes = str(result)
         if not bytes: break

         length = len(bytes)
         h.send('%X\r\n' % length)
         h.send(bytes + '\r\n')
         break
      h.send('0\r\n\r\n')

      resp = h.getresponse()
      status = resp.status # an int

      # Got a response, now decide how to act upon it
      if status in redirect: 
         location = resp.getheader('Location')
         uri = urlparse.urljoin(uri, location)
         host, port, path = parseuri(uri)

         # We may have to authenticate again
         if authorization: 
            authorization = None

      elif status in authenticate: 
         # If we've done this already, break
         if authorization: 
            # barf("Going around in authentication circles")
            print "Authentication failed"
            return False

         if not (username and password): 
            print "Need a username and password to authenticate with"
            return False

         # Get the scheme: Basic or Digest?
         wwwauth = resp.msg['www-authenticate'] # We may need this again
         wauth = wwwauth.lstrip(' \t') # Hence use wauth not wwwauth here
         wauth = wwwauth.replace('\t', ' ')
         i = wauth.index(' ')
         scheme = wauth[:i].lower()

         if scheme in set(['basic', 'digest']): 
            if verbose: 
               msg = "Performing %s Authentication..." % scheme.capitalize()
               print >> sys.stderr, msg
         else:
            print "Unknown authentication scheme: %s" % scheme
            return False

         if scheme == 'basic': 
            import base64
            userpass = username + ':' + password
            userpass = base64.encodestring(userpass).strip()
            authorized, authorization = True, 'Basic ' + userpass

         elif scheme == 'digest': 
            if verbose: 
               msg = "uses fragile, undocumented features in urllib2"
               print >> sys.stderr, "Warning! Digest Auth %s" % msg

            import urllib2 # See warning above

            passwd = type('Password', (object,), {
               'find_user_password': lambda self, *args: (username, password), 
               'add_password': lambda self, *args: None
            })()

            xreq = type('Request', (object,), { 
               'get_full_url': lambda self: uri, 
               'has_data': lambda self: None, 
               'get_method': lambda self: 'PUT', 
               'get_selector': lambda self: path
            })()

            # Cf. urllib2.AbstractDigestAuthHandler.retry_http_digest_auth
            auth = urllib2.AbstractDigestAuthHandler(passwd)
            token, challenge = wwwauth.split(' ', 1)
            chal = urllib2.parse_keqv_list(urllib2.parse_http_list(challenge))
            userpass = auth.get_authorization(xreq, chal)
            authorized, authorization = True, 'Digest ' + userpass

      elif status in okay: 
         if (username and password) and (not authorized): 
            msg = "Warning! The supplied username and password went unused"
            print >> sys.stderr, msg

         if verbose: 
            resultLine = "Success! Resource %s"
            statuses = {200: 'modified', 201: 'created', 204: 'modified'}
            print resultLine % statuses[status]

            statusLine = "Response-Status: %s %s"
            print statusLine % (status, resp.reason)

            body = resp.read(58)
            body = body.rstrip('\r\n')
            body = body.encode('string_escape')

            if len(body) >= 58: 
               body = body[:57] + '[...]'

            bodyLine = 'Response-Body: "%s"'
            print bodyLine % body
         break

      # @@ raise PutError, do the catching in main?
      else: 
        print 'Got "%s %s"' % (status, resp.reason)
        return False

      tries += 1
      if tries >= 50: 
         print "Too many redirects"
         return False

    print str(result)
    return True
