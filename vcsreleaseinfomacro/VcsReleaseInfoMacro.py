from trac.core import *
from trac.util import escape, Markup
from trac.wiki.api import parse_args
from trac.wiki.macros import WikiMacroBase
from trac.wiki.formatter import wiki_to_html
from trac.util import format_datetime
from StringIO import StringIO
from operator import itemgetter, attrgetter
from trac.versioncontrol import Node
from trac.versioncontrol.api import RepositoryManager

class VcsReleaseInfoMacro(WikiMacroBase):
    """ Provides the macro VcsReleaseInfoMacro to display latest releases from VCS path.

    Usage:
    {{{
       [[VcsReleaseInfoMacro(path[,limit[,rev]])]]
    }}}

    """

    def get_releases(self, repo, path, rev):
        tagsnode = repo.get_node(path + "/tags", rev)
        releases = []
        # http://trac.edgewall.org/wiki/TracDev/VersionControlApi
        # http://trac.edgewall.org/browser/trunk/trac/versioncontrol/api.py#latest
        for node in tagsnode.get_entries():
            if node.kind != Node.DIRECTORY:
                continue

            cs = repo.get_changeset(node.rev)
            releases.append({
                'version' : node.get_name(),
                'time' : node.get_last_modified(),
                'rev' : node.rev,
                'author' : cs.author or 'anonymous',
                'message' : cs.message,
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

    def expand_macro(self, formatter, name, content):
        req = formatter.req
        args, kwargs = parse_args(content)
        args += [None, None, None]
        path, limit, rev = args[:3]
        limit = kwargs.pop('limit', limit)
        rev = kwargs.pop('rev', rev)

        if 'CHANGESET_VIEW' not in req.perm:
            return Markup('<i>Releases not available</i>')

        rm = RepositoryManager(self.env)
        reponame, repo, path = rm.get_repository_by_path(path);

        if rev is None:
            rev = repo.get_youngest_rev()
        rev = repo.normalize_rev(rev)
        path = repo.normalize_path(path)
        if limit is None:
            limit = 20
        else:
            limit = int(limit)

        releases = self.get_releases(repo, path, rev)

        # limit the releases after they have been sorted
        releases = releases[:1+limit]
        items = []
        releases = [None] + releases + [None]
        path = reponame.rstrip('/') + path.lstrip('/')
        for i in xrange(len(releases) - 2):
            prev, cur, next = releases[i : i + 3]

            if prev == None and next == None:
                # no releases yet, just show trunk
                items.append(
                    " * "
                    " [/browser/%(path)s/trunk trunk]"
                    " @[changeset:%(rev)s %(rev)s]"
                    " ("
                    "[/log/%(path)s/trunk changes]"
                    " [/changeset?new_path=%(path)s/trunk diffs]"
                    ")"
                % {
                    'path': path,
                    'rev': cur['rev'],
                })
            elif prev == None:
                # first entry = trunk
                items.append(
                    " * "
                    " [/browser/%(path)s/trunk trunk]"
                    " @[changeset:%(rev)s %(rev)s]"
                    " ("
                    "[/log/%(path)s/trunk?stop_rev=%(stop_rev)s changes]"
                    " [/changeset?old_path=%(path)s/tags/%(old_tag)s&new_path=%(path)s/trunk diffs]"
                    ")"
                % {
                    'path': path,
                    'rev' : cur['rev'],
                    'old_tag' : next['version'],
                    'stop_rev' : next['rev'],
                })
            elif next != None:
                # regular releases
                items.append(
                    " * '''%(date)s'''"
                    " [/log/%(path)s/tags/%(new_tag)s %(new_tag)s]"
                    " @[changeset:%(rev)s %(rev)s]"
                    " by %(author)s"
                    " ("
                    "[/log/%(path)s/trunk?rev=%(rev)s&stop_rev=%(stop_rev)s changes]"
                    " [/changeset?old_path=%(path)s/tags/%(old_tag)s&new_path=%(path)s/tags/%(new_tag)s diffs]"
                    ")"
                % {
                    'path': path,
                    'date': cur['time'].strftime('%Y-%m-%d'),
                    'rev' : cur['rev'],
                    'stop_rev' : next['rev'],
                    'old_tag' : next['version'],
                    'new_tag' : cur['version'],
                    'author': cur['author'],
                })
            else:
                # last release
                items.append(
                    " * '''%(date)s'''"
                    " [/log/%(path)s/tags/%(new_tag)s?rev=%(rev)s&mode=follow_copy %(new_tag)s]"
                    " @[changeset:%(rev)s %(rev)s]"
                    " by %(author)s"
                % {
                    'path': path,
                    'date': cur['time'].strftime('%Y-%m-%d'),
                    'rev' : cur['rev'],
                    'new_tag' : cur['version'],
                    'author': cur['author'],
                })

        return '<div class="releases">\n' + str(wiki_to_html("\n".join(items), self.env, req))  + '</div>\n'

# vim:et:ts=4:sw=4
