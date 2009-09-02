# -*- coding: utf-8 -*-
import re

from trac.wiki.formatter import wiki_to_html
from trac.wiki.macros import WikiMacroBase
from genshi.builder import tag
from util import validate_acl
import ezPyCrypto

class GringottMacro(WikiMacroBase):
  """This macro will take a single argument and display the content
  stored in that 'grottlet' if you are authorised to view it.

  This is used e.g. to store more sensitive information than you would
  generally feel comfortable placing in an open wiki.

  Access to individual 'grottlets can be controlled via an ACL.
  """

  def expand_macro(self, formatter, names, content):
    if not content:
      edit = ''
      text = "''Gringlet Name Missing''"
      acl = ''
    elif not re.match(r'^[a-zA-Z0-9]+$', content):
      edit = ''
      text = tag.em("Invalid Gringlet Name - only letters and numbers allowed")
      acl = ''
    else:
      db = self.env.get_db_cnx()
      cursor = db.cursor()
      cursor.execute('SELECT text,acl FROM gringotts WHERE name=%s AND version='
                     '(SELECT MAX(version) FROM gringotts WHERE name=%s)',
                     (content, content))

    try:
      text,acl = cursor.fetchone()
      key = str(self.config.get('gringotts', 'key'))
      k = ezPyCrypto.key(key)
      text = wiki_to_html(k.decStringFromAscii(text), self.env, formatter.req)
      edit = 'Edit'
    except:
      edit = 'Create'
      text = tag.em("No Gringlet called \"%s\" found" % content)
      acl = ''
    
    if acl:
      if not validate_acl(formatter.req, acl):
        text = tag.em("You do not have permission to view the \"%s\" Gringlet." % content)
        edit = ''
    
    control = None
    if edit:
      control = tag.div(tag.a(edit, href=(formatter.href.gringotts() + "/" + content + "?action=edit")), class_="gringottcontrol")
    
    
    # Use eight divs for flexible frame styling
    return tag.div(
            tag.div(
             tag.div(
              tag.div(
               tag.div(
                tag.div(
                 tag.div(
                  tag.div(
                   tag.div(text, class_="gringottcontent") + control,
                  class_="gringott"),
                 class_="gringott"),
                class_="gringott"),
               class_="gringott"),
              class_="gringott"),
             class_="gringott"),
            class_="gringott"),
           class_="gringottframe")
