# vim: expandtab
from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from tracrpc.api import IXMLRPCHandler
from acct_mgr.htfile import HtPasswdStore
from acct_mgr.api import IPasswordStore
import sys, inspect


def try_int(s):
    "Convert to integer if possible."
    try: return int(s)
    except: return s

def natsort_key(s):
    "Used internally to get a tuple by which s is sorted."
    import re
    return map(try_int, re.findall(r'(\d+|\D+)', s))

def natcmp(a, b):
    "Natural string comparison, case sensitive."
    return cmp(natsort_key(a), natsort_key(b))

def natcasecmp(a, b):
    "Natural string comparison, ignores case."
    return natcmp(a.lower(), b.lower())

def natsort(seq, cmp=natcmp):
    "In-place natural string sort."
    seq.sort(cmp)

def natsorted(seq, cmp=natcmp):
    "Returns a copy of seq, sorted by natural string sort."
    temp = list(seq)
    natsort(temp, cmp)
    return temp


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

        tagspace = TagEngine(self.env).tagspace.wiki

        out = StringIO()
        pages = tagspace.get_tagged_names(tags=['type'])
        pages = sorted(pages)

        out.write('<form style="text-align: right; padding-top: 1em; margin-right: 5em;" method="get">')
        out.write('<span style="font-size: xx-small">')
        out.write('Show hacks for releases: ')
        releases = natsorted(tagspace.get_tagged_names(tags=['release']))
        if 'update_th_filter' in req.args:
            show_releases = req.args.get('release', ['0.10'])
            if isinstance(show_releases, basestring):
                show_releases = [show_releases]
            req.session['th_release_filter'] = ','.join(show_releases)
        else:
            show_releases = req.session.get('th_release_filter', '0.12').split(',')
        for version in releases:
            checked = version in show_releases
            out.write('<input type="checkbox" name="release" value="%s"%s>%s\n' % (version, checked and ' checked' or '', version))
        out.write('<input name="update_th_filter" type="submit" style="font-size: xx-small; padding: 0; border: solid 1px black" value="Update"/>')
        out.write('</span>')
        out.write('</form>')
        for i, pagename in enumerate(pages):
            page = WikiPage(self.env, pagename)
            if page.text:
                topmargin = '0em'
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
                body = wiki_to_html(body, self.env, req)
                # Dear God, the horror!
                for line in body.splitlines():
                    show = False
                    for release in show_releases:
                        self.env.log.debug(release)
                        if '>%s</a>' % release in line:
                            show = True
                            break
                    if show or not '<li>' in line:
                        out.write(line)

                out.write('</fieldset>\n')

        return out.getvalue()

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
                from tractags.api import TagEngine
                tagspace = TagEngine(self.env).tagspace.wiki

                tagspace.add_tags(None, user, ['user'])
                page.text = '''= %(user)s =\n\n[[ListTagged(%(user)s)]]\n\n[[TagIt(user)]]''' % {'user' : user}
                page.save(user, 'New user %s registered' % user, None)
                self.env.log.debug("New user %s registered" % user)
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
        yield ('XML_RPC', ((dict,str),), self.getDetails)

    # Other methods
    def getReleases(self, req):
        """ Return a list of Trac releases TracHacks is aware of. """
        from tractags.api import TagEngine
        return TagEngine(self.env).tagspace.wiki.get_tagged_names(['release'])

    def getTypes(self, req):
        """ Return a list of known Hack types. """
        from tractags.api import TagEngine
        return TagEngine(self.env).tagspace.wiki.get_tagged_names(['type'])

    def getHacks(self, req, release, type):
        """ Fetch a list of hacks for Trac release, of type. """
        from trac.versioncontrol.api import Node
        from tractags.api import TagEngine
        repo = self.env.get_repository(req.authname)
        wikitags = TagEngine(self.env).tagspace.wiki
        repo_rev = repo.get_youngest_rev()
        releases = wikitags.get_tagged_names([release])
        types = wikitags.get_tagged_names([type])
        for plugin in releases.intersection(types):
            if plugin.startswith('tags/'): continue
            path = '%s/%s' % (plugin.lower(), release)
            rev = 0
            if repo.has_node(str(path), repo_rev):
                node = repo.get_node(path)
                rev = node.rev
            yield (plugin, rev)

    def getDetails(self, req, hack):
        """ Fetch hack details. Returns dict with name, dependencies and
            description. """
        from tractags.api import TagEngine
        wikitags = TagEngine(self.env).tagspace.wiki
        tags = wikitags.get_tags(hack)
        types = self.getTypes()
        hacks = wikitags.get_tagged_names(types)

        dependencies = hacks.intersection(tags)
        href, htmllink, description = wikitags.name_details(hack)
        return {'name': hack, 'dependencies': tuple(dependencies),
                'description': description}
