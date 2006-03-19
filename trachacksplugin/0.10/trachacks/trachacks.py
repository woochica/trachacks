# vim: expandtab
from trac.core import *
from trac.wiki.api import IWikiMacroProvider
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
        from trac.wiki.model import WikiPage
        from trac.util import Markup
        from tractags.api import TagEngine
        import re

        tagengine = TagEngine(self.env)

        out = StringIO()
        pages = list(tagengine.wiki.get_tagged_names('type'))
        pages.sort()

        for i, pagename in enumerate(pages):
            page = WikiPage(self.env, pagename)
            if page.text:
                if i > 0:
                    topmargin = '0em'
                else:
                    topmargin = '2em'
                if i < len(pages) - 1:
                    bottommargin = '0em'
                else:
                    bottommargin = '2em'
                    
                out.write('<fieldset style="padding: 1em; margin: %s 5em %s 5em; border: 1px solid #999;">\n' % (topmargin, bottommargin))
                body = page.text
                title = re.search('=+\s([^=]*)=+', body)
                if title:
                    title = title.group(1).strip()
                    body = re.sub('=+\s([^=]*)=+', '', body, 1)
                else:
                    title = pagename
                body = re.sub('\\[\\[TagIt.*', '', body)
                out.write('<legend style="color: #999;"><a href="%s">%s</a></legend>\n' % (self.env.href.wiki(pagename), title))
                out.write('%s\n' % wiki_to_html(body, self.env, req))
                out.write('</fieldset>\n')
        return out.getvalue()

try:
    from acct_mgr.htfile import HtPasswdStore
    from acct_mgr.api import IPasswordStore
    class TracHacksAccountManager(HtPasswdStore):
        """ Do some basic validation on new users, and create a new user page. """
        implements(IPasswordStore)

        # IPasswordStore
        def config_key(self):
            return 'trachacks-htpasswd'

        def set_password(self, user, password):
            import re
            if len(user) < 3:
                raise TracError('user name must be at least 3 characters long')
            if not re.match(r'^\w+$', user):
                raise TracError('user name must consist only of alpha-numeric characters')
            if user not in self.get_users():
                from trac.wiki.model import WikiPage
                db = self.env.get_db_cnx()
                page = WikiPage(self.env, user, db=db)
                # User creation with existing page
                if page.exists:
                    raise TracError('wiki page "%s" already exists' % user)
                else:
                    tagengine = TagEngine(self.env)

                    tagengine.wiki.add_tag(None, user, 'user')
                    page.text = '''= %(user)s =\n\n[[ListTags(%(user)s)]]\n\n[[TagIt(user)]]''' % {'user' : user}
                    page.save(user, 'New user %s registered' % user, None)
                    self.env.log.debug("New user %s registered" % user)
            HtPasswdStore.set_password(self, user, password)

        def delete_user(self, user):
            HtPasswdStore.delete_user(self, user)
except ImportError:
    pass

class TracHacksRPC(Component):
    """ Allow inspection of hacks on TracHacks. """
    implements(IXMLRPCHandler)

    def xmlrpc_namespace(self):
        return 'trachacks'

    def xmlrpc_methods(self):
        yield ('XML_RPC', ((list, str, str),), self.getHacks)
        yield ('XML_RPC', ((list,),), self.getReleases)
        yield ('XML_RPC', ((list,),), self.getTypes)
        yield ('XML_RPC', ((dict,str),), self.getDetails)

    # Other methods
    def getReleases(self):
        """ Return a list of Trac releases TracHacks is aware of. """
        from tractags.api import TagEngine
        return TagEngine(self.env).wiki.get_tagged_names('release')

    def getTypes(self):
        """ Return a list of known Hack types. """
        from tractags.api import TagEngine
        return TagEngine(self.env).wiki.get_tagged_names('type')

    def getHacks(self, req, release, type):
        """ Fetch a list of hacks for Trac release, of type. """
        from trac.versioncontrol.api import Node
        from tractags.api import TagEngine
        repo = self.env.get_repository(req.authname)
        wikitags = TagEngine(self.env).wiki
        repo_rev = repo.get_youngest_rev()
        releases = wiki.get_tagged_names(release)
        types = wiki.get_tagged_names(type)
        for plugin in releases.intersection(types):
            if plugin.startswith('tags/'): continue
            path = '%s/%s' % (plugin.lower(), release)
            rev = 0
            if repo.has_node(path, repo_rev):
                node = repo.get_node(path)
                rev = node.rev
            yield (plugin, rev)

    def getDetails(self, req, hack):
        """ Fetch hack dependencies. """
        from tractags.api import TagEngine
        wikitags = TagEngine(self.env).wiki
        tags = wikitags.get_tags(hack)
        types = self.getTypes()
        hacks = wikitags.get_tagged_names(*types)

        dependencies = hacks.intersection(tags)
        href, htmllink, description = wikitags.name_details(hack)
        return {'name': hack, 'dependencies': tuple(dependencies),
                'description': description}
