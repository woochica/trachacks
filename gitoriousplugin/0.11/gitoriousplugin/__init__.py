import re

from genshi.builder import tag

from trac.core import *
from trac.config import Option
from trac.util.text import shorten_line
from trac.wiki.api import IWikiSyntaxProvider
from trac.web.chrome import INavigationContributor
from trac.util.translation import _

class GitoriousPlugin(Component):
    implements(INavigationContributor, IWikiSyntaxProvider)

    project = Option("gitorious", "project", None)
    repo = Option("gitorious", "repository", None)

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'browser'

    def get_navigation_items(self, req):
        if 'BROWSER_VIEW' not in req.perm:
            return
        if self.project is None:
            self.env.log.warning("You did not set the 'project' name in the "
                                 "'[gitorious]' section, the Gitorious plugin "
                                 "will be disabled")
            return
        href = self._format_gitorious(path="/", obj_type="dir")
        yield ('mainnav', 'browser', tag.a(_('Browse Source'), href=href))


    # IWikiSyntaxProvider methods

    def get_wiki_syntax(self):
        return []

    def get_link_resolvers(self):
        """Replaces the TracBrowser link resolvers."""
        if self.project is None:
            self.env.log.error("You did not set the 'project' name in the "
                               "'[gitorious]' section, the Gitorious plugin "
                               "will be disabled")
            return []
        return [('repos', self._format_browser_link),
                ('export', self._format_export_link),
                ('source', self._format_browser_link),
                ('browser', self._format_browser_link),
                ('changeset', self._format_changeset_link),
                ]

    def _format_export_link(self, formatter, ns, export, label):
        export, query, fragment = formatter.split_link(export)
        if ':' in export:
            rev, path = export.split(':', 1)
        elif '@' in export:
            path, rev = export.split('@', 1)
        else:
            rev = None
            path = export
        return tag.a(label, class_='source',
                     href=formatter.href.export(rev, path) + fragment)

    def _format_browser_link(self, formatter, ns, path, label):
        path, query, fragment = formatter.split_link(path)
        rev = marks = None
        match = self.PATH_LINK_RE.match(path)
        if match:
            path, rev, marks = match.groups()
        if fragment:
            fragment = fragment.replace("L","line")
        if path.endswith("/"):
            obj_type = "dir"
        else:
            obj_type = "file"
        href = self._format_gitorious(path=path, rev=rev, marks=marks,
                                      obj_type=obj_type) + fragment
        return tag.a(label, class_='source', href=href)

    PATH_LINK_RE = re.compile(r"([^@#:]*)"     # path
                              r"[@:]([^#:]+)?" # rev
                              r"(?::(\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*))?" # marks
                              )

    def _format_changeset_link(self, formatter, ns, chgset, label,
                               fullmatch=None):
        intertrac = formatter.shorthand_intertrac_helper(ns, chgset, label,
                                                         fullmatch)
        if intertrac:
            return intertrac
        chgset, params, fragment = formatter.split_link(chgset)
        sep = chgset.find('/')
        if sep > 0:
            rev, path = chgset[:sep], chgset[sep:]
        else:
            rev, path = chgset, None
        if 'CHANGESET_VIEW' in formatter.perm('changeset', rev):
            try:
                changeset = self.env.get_repository().get_changeset(rev)
                title = shorten_line(changeset.message)
            except TracError, e:
                title = None
            href = self._format_gitorious(path=path, rev=rev,
                                          obj_type="changeset")
            return tag.a(label, class_="changeset", href=href, title=title)
        return tag.a(label, class_="missing changeset")


    def _format_gitorious(self, path=None, rev=None, marks=None,
                          branch="master", obj_type="file", export=False):
        """
        TODO: marks are unsupported, and the 'master' branch is unchangeable.
        """
        href = ["http://gitorious.org", self.project]

        if self.repo is None:
            self.env.log.debug("Configuration variable 'repository' not set, "
                               "assuming '%s'" % self.project)
            href.append(self.project)
        else:
            href.append(self.repo)

        if obj_type == "file":
            href.append("blobs")
        elif obj_type == "dir":
            href.append("trees")
        elif obj_type == "changeset":
            href.append("commit")
        else:
            self.env.log.warning("_get_action called with an unknown "
                                 "object type, assuming 'file'")
            href.append("blobs")

        if export:
            if href[-1] == "blobs":
                href.append("raw")
            else:
                self.env.log.warning("Can't export a subdirectory or "
                                     "a changeset with Gitorious")
        if rev:
            href.append(rev)

        if path:
            if path.startswith("/"):
                path = path[1:]
            if obj_type == "changeset":
                href[-1] = "%s?diffmode=sidebyside#%s" % (href[-1], path)
            else:
                href.append(branch)
                href.append(path)

        return "/".join([p for p in href if p is not None])

