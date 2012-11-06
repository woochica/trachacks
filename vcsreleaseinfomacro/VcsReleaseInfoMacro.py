from trac.core import *
from trac.util import escape, Markup
from trac.wiki.api import parse_args
from trac.wiki.macros import WikiMacroBase
from trac.wiki.formatter import wiki_to_html
from trac.wiki.model import WikiPage
from trac.util import format_datetime, to_unicode
from StringIO import StringIO
from operator import itemgetter, attrgetter
from trac.versioncontrol import Node
from trac.versioncontrol.api import RepositoryManager

# NOTE to self: debug: self.env.log.debug('woot');

class VcsReleaseInfoMacro(WikiMacroBase):
    """ Provides the macro VcsReleaseInfoMacro to display latest releases from VCS path.

    Usage:
    {{{
       [[VcsReleaseInfoMacro(path[, limit, package = PACKAGE])]]
    }}}

    """

    def __init__(self):
        # baseurl for cvsweb for rpm .spec's
        # TODO: make this configurable
        self.spec_baseurl = None

    def get_releases(self, repo, path, rev):
        tagsnode = repo.get_node(path + "/tags", rev)
        releases = []
        # http://trac.edgewall.org/wiki/TracDev/VersionControlApi
        # http://trac.edgewall.org/browser/trunk/trac/versioncontrol/api.py#latest
        for node in tagsnode.get_entries():
            if node.kind != Node.DIRECTORY:
                continue

            cs = repo.get_changeset(node.created_rev)
            releases.append({
                'version' : node.get_name(),
                'time' : node.get_last_modified(),
                'rev' : node.created_rev,
                'author' : cs.author or 'anonymous',
                'message' : cs.message,
                'props' : cs.get_properties(),
            })
        releases = sorted(releases, key=itemgetter('time'), reverse=True)

        # insert trunk info
        node = repo.get_node(path + "/trunk", rev)
        releases.insert(0, {
            'version' : node.get_name(),
            'time' : node.get_last_modified(),
            'rev' : node.rev,
        })

        return releases

    # generate cvsweb annotate link for spec
    def specurl_annotate(self, props):
        if not self.spec_baseurl:
            return None

        if not props.has_key('props'):
            return None
        revprops = props['props']
        if not revprops.has_key('rpm:spec') or not revprops.has_key('rpm:cvsrev'):
            return None

        return "%s/%s?annotate=%s" % (self.spec_baseurl, revprops['rpm:spec'], revprops['rpm:cvsrev'])

    # generate cvsweb diff link for spec
    def specurl_diff(self, prev, cur):
        if not self.spec_baseurl:
            return None

        if not prev.has_key('props') or not cur.has_key('props'):
            return None

        revprops = prev['props']
        if not revprops.has_key('rpm:spec') or not revprops.has_key('rpm:cvsrev'):
            return None
        r1 = revprops['rpm:cvsrev']

        revprops = cur['props']
        if not revprops.has_key('rpm:spec') or not revprops.has_key('rpm:cvsrev'):
            return None
        r2 = revprops['rpm:cvsrev']

        return "%s/%s.diff?r1=%s;r2=%s;f=h" % (self.spec_baseurl, revprops['rpm:spec'], r1, r2)

    def expand_macro(self, formatter, name, content):
        req = formatter.req
        args, kwargs = parse_args(content)
        args += [None, None]
        path, limit = args[:2]
        limit = kwargs.pop('limit', limit)
        package = kwargs.pop('package', None)

        if 'CHANGESET_VIEW' not in req.perm:
            return Markup('<i>Releases not available</i>')

        rm = RepositoryManager(self.env)
        reponame, repo, path = rm.get_repository_by_path(path);

        rev = repo.get_youngest_rev()
        rev = repo.normalize_rev(rev)
        path = repo.normalize_path(path)
        if limit is None:
            limit = 20
        else:
            limit = int(limit)

        releases = self.get_releases(repo, path, rev)

        # limit the releases after they have been sorted
        releases = releases[:1 + limit]
        items = []
        releases = [None] + releases + [None]

        # some extra checks to avoid using double-slashes
        if reponame == '':
            if path == '/':
                path = ''
            else:
                path = '/' + path
        elif path == '/':
            path = '/' + reponame.rstrip('/')
        else:
            path = '/' + reponame.rstrip('/') + '/' + path.lstrip('/')

        if not package:
            package = path.split("/")[-1]

        for i in xrange(len(releases) - 2):
            prev, cur, next = releases[i : i + 3]

            if prev == None and next == None:
                # no releases yet, just show trunk
                items.append(
                    " * "
                    " [/browser%(path)s/trunk trunk]"
                    " @[changeset:%(rev)s/%(reponame)s %(rev)s]"
                    " ("
                    "[/log%(path)s/trunk changes]"
                    " [/changeset?new_path=%(path)s/trunk diffs]"
                    ")"
                % {
                    'reponame' : reponame,
                    'path': path,
                    'rev': cur['rev'],
                })
            elif prev == None:
                # first entry = trunk
                items.append(
                    " * "
                    " [/browser%(path)s/trunk trunk]"
                    " @[changeset:%(rev)s/%(reponame)s %(rev)s]"
                    " ("
                    "[/log%(path)s/trunk?revs=%(stop_rev)s-%(rev)s changes]"
                    " [/changeset?old_path=%(path)s/tags/%(old_tag)s&new_path=%(path)s/trunk diffs]"
                    ")"
                % {
                    'reponame' : reponame,
                    'path': path,
                    'rev' : cur['rev'],
                    'old_tag' : next['version'],
                    'stop_rev' : next['rev'],
                })
            elif next != None:
                # regular releases
                release_page = 'release/%s-%s' % (package, cur['version'])
                page = WikiPage(self.env, release_page)
                if page.exists:
                    release_link = " [wiki:%s release notes]" % (release_page)
                else:
                    release_link = ""

                items.append(
                    " * '''%(date)s'''"
                    " [/log%(path)s/tags/%(new_tag)s %(new_tag)s] "
                    " @[changeset:%(rev)s/%(reponame)s %(rev)s]"
                    " by %(author)s"
                    " ("
                    "[/log%(path)s/trunk?revs=%(stop_rev)s-%(rev)s changes]"
                    " [/changeset?old_path=%(path)s/tags/%(old_tag)s&new_path=%(path)s/tags/%(new_tag)s diffs]"
                    "%(release_link)s"
                    ")"
                % {
                    'reponame' : reponame,
                    'path': path,
                    'date': cur['time'].strftime('%Y-%m-%d'),
                    'rev' : cur['rev'],
                    'stop_rev' : next['rev'],
                    'old_tag' : next['version'],
                    'new_tag' : cur['version'],
                    'author': cur['author'],
                    'release_link' : release_link,

                })
                url = self.specurl_annotate(cur);
                if url != None:
                    annotate = " spec: [%s annotate]" % url
                    items.append(annotate)
                    # check also diff link
                    url = self.specurl_diff(cur, next);
                    if url != None:
                        annotate = " [%s diff]" % url
                        items.append(annotate)
            else:
                # last release
                items.append(
                    " * '''%(date)s'''"
                    " [/log%(path)s/tags/%(new_tag)s?rev=%(rev)s&mode=follow_copy %(new_tag)s]"
                    " @[changeset:%(rev)s/%(reponame)s %(rev)s]"
                    " by %(author)s"
                % {
                    'reponame' : reponame,
                    'path': path,
                    'date': cur['time'].strftime('%Y-%m-%d'),
                    'rev' : cur['rev'],
                    'new_tag' : cur['version'],
                    'author': cur['author'],
                })

        return '<div class="releases">\n' + to_unicode(wiki_to_html("\n".join(items), self.env, req))  + '</div>\n'

# vim:et:ts=4:sw=4
