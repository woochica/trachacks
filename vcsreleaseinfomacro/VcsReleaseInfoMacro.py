from trac.core import *
from trac.util import escape, Markup
from trac.wiki.api import parse_args
from trac.wiki.macros import WikiMacroBase
from trac.wiki.formatter import wiki_to_html
from trac.util import format_datetime
from StringIO import StringIO
from operator import itemgetter, attrgetter

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
            cs = repo.get_changeset(node.rev)
            releases.append({
                'version' : node.get_name(),
                'time' : node.get_last_modified(),
                'rev' : node.rev,
                'author' : cs.author,
                'message' : cs.message,
            })

        return sorted(releases, key=itemgetter('time'), reverse=True)

    def expand_macro(self, formatter, name, content):
        req = formatter.req
        args, kwargs = parse_args(content)
        args += [None, None]
        path, limit, rev = args[:3]
        limit = kwargs.pop('limit', limit)
        rev = kwargs.pop('rev', rev)

        if 'CHANGESET_VIEW' not in req.perm:
            return Markup('<i>Releases not available</i>')

        repo = self.env.get_repository()

        if rev is None:
            rev = repo.get_youngest_rev()
        rev = repo.normalize_rev(rev)
        path = repo.normalize_path(path)
        if limit is None:
            limit = 10
        else:
            limit = int(limit)

        releases = self.get_releases(repo, path, rev)

        # limit the releases after they have been sorted
        releases = releases[:limit]

        items = []
        releases = [None] + releases + [None]
        for i in xrange(len(releases) - 2):
            prev, cur, next = releases[i : i + 3]

            if prev == None:
                # first entry = trunk
                items.append(
                    " * "
                    " [/log/%(path)s/trunk trunk]"
                    " ("
                    "[/log/%(path)s/trunk?stop_rev=%(stop_rev)s changes]"
                    " [/changeset?old_path=%(path)s/tags/%(old_tag)s&new_path=%(path)s/trunk diffs]"
                    ")"
                % {
                    'path': path,
                    'date': cur['time'].strftime('%Y-%m-%d'),
                    'old_tag' : cur['version'],
                    'stop_rev' : cur['rev'],
                })
            elif next != None:
                # regular releases
                items.append(
                    " * '''%(date)s'''"
                    " [/log/%(path)s/tags/%(new_tag)s %(new_tag)s]"
                    " by %(author)s"
                    " ("
                    "[/log/%(path)s/trunk?rev=%(rev)s&stop_rev=%(stop_rev)s changes]"
                    " [/changeset?old_path=%(path)s/tags/%(old_tag)s&new_path=%(path)s/tags/%(new_tag)s diffs]"
                    ")"
                % {
                    'path': path,
                    'date': cur['time'].strftime('%Y-%m-%d'),
                    'rev' : prev['rev'],
                    'stop_rev' : cur['rev'],
                    'old_tag' : cur['version'],
                    'new_tag' : prev['version'],
                    'author': cur['author'],
                })
            else:
                # last release
                items.append(
                    " * '''%(date)s'''"
                    " [/log/%(path)s/tags/%(new_tag)s?rev=%(rev)s&mode=follow_copy %(new_tag)s]"
                    " by %(author)s"
                % {
                    'path': path,
                    'date': cur['time'].strftime('%Y-%m-%d'),
                    'rev' : cur['rev'],
                    'stop_rev' : '',
                    'old_tag' : cur['version'],
                    'new_tag' : cur['version'],
                    'author': cur['author'],
                })

        return '<div class="releases">\n' + str(wiki_to_html("\n".join(items), self.env, req))  + '</div>\n'
