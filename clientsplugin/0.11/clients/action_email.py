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
from clients.action import IClientActionProvider


class ClientActionEmail(Component):
  implements(IClientActionProvider)

  client = None
  debug = False

  def get_name(self):
    return "Send Email"

  def get_description(self):
    return "Send an email to a certain list of addresses"

  def instance_options(self):
    yield {'name': 'XSLT', 'description': 'Formatting XSLT to convert the summary to an email'}

  def client_options(self):
    return []

  def init(self, instance, client):
    self.client = client
    return True

  def perform(self, summary):
    return None
