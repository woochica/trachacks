# vim: expandtab
from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from acct_mgr.htfile import HtPasswdStore
from acct_mgr.api import IPasswordStore
from tracrpc.api import IXMLRPCHandler
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
        self.env.log.debug(len(user))
        if len(user) < 3:
            raise TracError('user name must be at least 3 characters long')
        if not re.match(r'^\w+$', user):
            raise TracError('user name must consist only of alpha-numeric characters')
        self.env.log.debug("New user %s registered" % user)
        if user not in self.get_users():
            from trac.wiki.model import WikiPage
            db = self.env.get_db_cnx()
            page = WikiPage(self.env, user, db = db)
            # User creation with existing page
            if page.exists:
                raise TracError('wiki page "%s" already exists' % user)
            else:
                page.text = '''= %(user)s =\n\n[[ListTags(%(user)s)]]\n\n[[TagIt(user)]]''' % {'user' : user}
                page.save(user, 'New user %s registered' % user, None)
                cursor = db.cursor()
                cursor.execute('INSERT INTO wiki_namespace VALUES (%s, %s)', (user, 'user'))
        HtPasswdStore.set_password(self, user, password)

    def delete_user(self, user):
        HtPasswdStore.delete_user(self, user)

class TracHacksRPC(Component):
    """ Allow inspection of hacks on TracHacks. """
    implements(IXMLRPCHandler)

    def xmlrpc_namespace(self):
        return 'trachacks'

    def xmlrpc_methods(self):
        yield ('XML_RPC', ((list, str, str),), self.getHacks)
        yield ('XML_RPC', ((list,),), self.getReleases)
        yield ('XML_RPC', ((list,),), self.getTypes)

    # Other methods
    def getReleases(self):
        """ Return a list of Trac releases TracHacks is aware of. """
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT name FROM wiki_namespace WHERE namespace='release'")
        return [x[0] for x in cursor.fetchall()]

    def getTypes(self):
        """ Return a list of known Hack types. """
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT name FROM wiki_namespace WHERE namespace='type'")
        return [x[0] for x in cursor.fetchall()]

    def getHacks(self, req, release, type):
        """ Fetch a list of hacks for Trac release, of type. """
        from trac.versioncontrol.api import Node

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        repo = self.env.get_repository(req.authname)
        repo_rev = repo.get_youngest_rev()

        # Get releases and types
        releases = self.getReleases()
        types = self.getTypes()

        cursor.execute("SELECT name FROM wiki_namespace WHERE namespace=%s " \
                       "INTERSECT SELECT NAME FROM wiki_namespace WHERE " \
                       "namespace=%s", (release, type));
        for (plugin,) in cursor.fetchall():
            if plugin.startswith('tags/'): continue
            path = '%s/%s' % (plugin.lower(), release)
            rev = 0
            if repo.has_node(path, repo_rev):
                node = repo.get_node(path)
                rev = node.rev
            yield (plugin, rev)
