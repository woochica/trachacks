import imp
import inspect
import os
import re
try:
    set
except NameError:
    from sets import Set as set
from StringIO import StringIO

from trac.config import default_dir
from trac.core import *
from trac.util import sorted
from trac.util.datefmt import format_date
from trac.util.html import escape, html, Markup
from trac.wiki.api import IWikiMacroProvider, WikiSystem
from trac.wiki.model import WikiPage
from trac.wiki.formatter import wiki_to_html
from trac.wiki.macros import WikiMacroBase
from trac.web.chrome import add_stylesheet
from util import validate_acl
import ezPyCrypto

class GringottMacro(WikiMacroBase):
    """This macro will take a single argument and display the content
    stored in that 'grottlet' if you are authorised to view it.

    This is used e.g. to store more sensitive information than you would
    generally feel comfortable placing in an open wiki.

    Access to individual 'grottlets can be controlled via an ACL.
    """


    def render_macro(self, req, name, content):
        # args will be null if the macro is called without parenthesis.
        if not content:
            edit = ''
            text = "''Gringlet Name Missing''"
            acl = ''
        elif not re.match(r'^[a-zA-Z0-9]+$', content):
            edit = ''
            text = "<em>Invalid Gringlet Name - only letters and numbers allowed</em>"
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
                text = wiki_to_html(k.decStringFromAscii(text), self.env, req)
                edit = 'Edit'
            except:
                edit = 'Create'
                text = "<em>No Gringlet called &quot;%s&quot; found</em>" % content
                acl = ''
                
        if acl:
            if not validate_acl(req, acl):
                text = "<em>You do not have permission to view the &quot;%s&quot; Gringlet.</em>" % content
                edit = ''

        control = ''
        if edit:
            control = ('<div class="gringottcontrol">' + \
                       '<a href="%s/%s">' + edit + '</a>' + \
                       '</div>') % (req.href.gringotts(), content)

            
        # Use eight divs for flexible frame styling
        html = '<div class="gringottframe"><div class="gringott">' + \
               '<div class="gringott"><div class="gringott">' + \
               '<div class="gringott"><div class="gringott">' + \
               '<div class="gringott"><div class="gringott">' + \
               '<div class="gringottcontent">' + \
               text + \
               '</div>' + \
               control + \
               '</div></div></div></div></div></div></div></div>'
        return html
