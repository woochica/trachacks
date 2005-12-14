# vim: expandtab
from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from acct_mgr.htfile import HtPasswdStore
from acct_mgr.api import IPasswordStore
import sys, inspect

class TracHacksMacros(Component):
    """ List of meta types """
    implements(IWikiMacroProvider)

    # IWikiMacroProvider methods
    def get_macros(self):
        yield 'ListTypes'

    def get_macro_description(self, name):
        return "Main hack type listing"

    def render_macro(self, req, name, content):
        from StringIO import StringIO
        from trac.wiki import wiki_to_html
        import re
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT name FROM wiki_namespace WHERE namespace=\'type\' ORDER BY name')
        out = StringIO()
        pages = [x[0] for x in cursor.fetchall()]
        for i in range(0, len(pages)):
            page = pages[i]
            pcursor = db.cursor()
            pcursor.execute("SELECT text FROM wiki WHERE name='%s' ORDER BY version DESC LIMIT 1" % page)
            body = pcursor.fetchone()
            if body:
                if i > 0:
                    topmargin = '0em'
                else:
                    topmargin = '2em'
                if i < len(pages) - 1:
                    bottommargin = '0em'
                else:
                    bottommargin = '2em'
                    
                out.write('<fieldset style="padding: 1em; margin: %s 5em %s 5em; border: 1px solid #999;">\n' % (topmargin, bottommargin))
                body = body[0]
                title = re.search('=+\s([^=]*)=+', body)
                if title:
                    title = title.group(1).strip()
                    body = re.sub('=+\s([^=]*)=+', '', body, 1)
                else:
                    title = page
                body = re.sub('\\[\\[TagIt.*', '', body)
                out.write('<legend style="color: #999;"><a href="%s">%s</a></legend>\n' % (self.env.href.wiki(page), title))
                out.write('%s\n' % wiki_to_html(body, self.env, req))
                out.write('</fieldset>\n')
        return out.getvalue()

class TracHacksAccountManager(HtPasswdStore):
    """ Do some basic validation on new users, and create a new user page. """
    implements(IPasswordStore)

    # IPasswordStore
    def config_key(self):
        return 'trachacks-htpasswd'

    def set_password(self, user, password):
        # User creation with existing page
        if user not in self.get_users():
            from trac.wiki.model import WikiPage
            db = self.env.get_db_cnx()
            page = WikiPage(self.env, user, db = db)
            if page.version:
                raise TracError('wiki page "%s" already exists' % user)
            else:
                page.text = '''= %(user)s =\n\n[[ListTags(%(user)s)]]\n\n[[TagIt(user)]]''' % {'user' : user}
                page.save(user, 'New user %s registered' % user, None)
                cursor = db.cursor()
                cursor.execute('INSERT INTO wiki_namespace VALUES (%s, %s)', (user, 'user'))
        HtPasswdStore.set_password(self, user, password)

    def delete_user(self, user):
        HtPasswdStore.delete_user(self, user)
