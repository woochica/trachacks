import re

from trac.core import *
from trac.util import escape, Markup
from trac.web.api import IRequestHandler
from trac.wiki.model import WikiPage
from trac.versioncontrol.web_ui.log import LogModule

class ChangesetFeedsModule(Component):
    implements(IRequestHandler)
    class FakeEnv(object):
        def __init__(self, env, pred):
            self.env = env
            self.pred = pred
            self.repos = None
        def get_repository(self, authname):
            self.repos = self.env.get_repository(authname)
            #return repos
            return ChangesetFeedsModule.FilteringRepos(self.repos, self._filter)
        def _filter(self, items):
            for path,rev,chg in items:
                if self.pred(path):
                    yield path,rev,chg
                    continue
                chgset = self.repos.get_changeset(rev)
                for chg_path,_,_,_,_ in chgset.get_changes():
                    if self.pred(chg_path):
                        yield path,rev,chg
                        break
        def __getitem__(self, name):
            return self.env[name]
        def __getattr__(self, name):
            return getattr(self.env, name)
    class FilteringRepos(object):
        def __init__(self, repos, filter):
            self.repos = repos
            self.filter = filter
            self.repos.log.debug('filtering')
        def get_path_history(self, path, rev=None, limit=None):
            return self.filter(self.repos.get_path_history(path, rev, limit))
        def get_node(self, path, rev=None):
            return ChangesetFeedsModule.FilteringNode(self.repos.get_node(path, rev), self.filter)
        def __getattr__(self, name):
            return getattr(self.repos, name)
    class FilteringNode(object):
        def __init__(self, node, filter):
            self.node = node
            self.filter = filter
        def get_history(self, limit=None):
            return self.filter(self.node.get_history(limit))
        def __getattr__(self, name):
            return getattr(self.node, name)

    def match_request(self, req):
        match = re.match(r'/changesetrss/(.+)', req.path_info)
        if match:
            req.args['filter'] = match.group(1)
            return 1

    def process_request(self, req):
        filter_page = WikiPage(self.env, req.args['filter'].value)
        self.log.debug(filter_page.name)
        if not filter_page.exists:
            raise TracError(Markup('Filter page "%s" not found', filter_page.name))
        self.log.debug(filter_page.text)
        filters = filter_page.text
        filters = filters.split('{{{', 1)[1].split('}}}', 1)[0].splitlines()
        filter_re = '|'.join('(?:%s)' % f for f in filters if f and not f.startswith('#'))
        self.log.debug(filter_re)
        filter_re = re.compile('|'.join('(?:%s)' % f for f in filters if f))
        pred = filter_re.search
        req.args['format'] = 'rss'
        req.args['path'] = '/'
        log_module = LogModule(self.env)
        log_module.env = ChangesetFeedsModule.FakeEnv(self.env, pred)
        return log_module.process_request(req)
