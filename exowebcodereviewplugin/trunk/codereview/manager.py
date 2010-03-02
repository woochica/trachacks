# codereviewmanager.py

import re

from trac.core import *
from trac.web import IRequestHandler
from trac.perm import IPermissionRequestor
from trac.web.chrome import ITemplateProvider, INavigationContributor

class CodeReviewManager(Component):
    implements(IRequestHandler,
               ITemplateProvider,
               INavigationContributor,
               IPermissionRequestor)

    def get_active_navigation_item(self, req):
        return 'CodeReview'

    def get_navigation_items(self, req):
        return []

    def get_permission_actions(self):
        return ['CODE_REVIEW_VIEW',]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('cr', resource_filename(__name__, 'htdocs'))]

    def match_request(self, req):
        return req.path_info.lower() == '/codereviewmanager'

    def process_request(self, req):
        req.perm.assert_permission('CODE_REVIEW_ADMIN')
        self._render_nav(req)
        if req.args.has_key('action'):
            if req.args.get('action') == 'config':
                return self._config(req)
            else:
                req.redirect(self.env.href.CodeReviewManager())
                return
        req.hdf['action'] = 'main'
        req.hdf['title'] = 'CodeReviewManager'
        self._render_config(req)
        return 'codereviewmanager.cs', None

    def _render_config(self, req):
        req.hdf['absurl'] = self.env.config.get('codereview', 'absurl')
        req.hdf['start_rev'] = self.env.config.get('codereview', 'start_rev')
        req.hdf['team_list'] = self.env.config.get('codereview', 'team_list')
        req.hdf['notify_enabled'] = self.env.config.get('codereview', 'notify_enabled')
        req.hdf['config.href'] = self.env.href.CodeReviewManager()
        
    def _render_nav(self, req):
        req.hdf['main.href'] = self.env.href.CodeReview()
        req.hdf['completed.href'] = self.env.href.CodeReview(completed='on')
        req.hdf['manager.href'] = self.env.href.CodeReviewManager()
        req.hdf['main'] = 'no'
        req.hdf['completed'] = 'no'
        req.hdf['manager'] = 'yes'

    def _config(self, req):
        ini = {}
        for k in ('absurl', 'team_list'):
            if req.args.has_key(k):
                if '\n' not in req.args.get(k):
                    ini[k] = req.args.get(k).strip()
                else:
                    ini[k] = req.args.get(k).split('\n', 1)[0].strip()

        if req.args.get('notify_enabled', '') in ('true', 'false'):
            ini['notify_enabled'] = req.args.get('notify_enabled')
        else:
            ini['notify_enabled'] = "false"

        if req.args.has_key('start_rev'):
            try:
                start_rev = int(req.args.get('start_rev').strip())
            except:
                start_rev = 0
            if start_rev < 0:
                ini['start_rev'] = '0'
            else:
                ini['start_rev'] = str(start_rev)
                
        for k, v in ini.items():
            self.env.config.set('codereview', k, v)
        self.env.config.save()

        req.hdf['title'] = 'Configure update successful'
        req.hdf['description'] = req.hdf['title']
        req.hdf['action'] = 'configok'
        req.hdf['manager_href'] = self.env.href.CodeReviewManager()
        return 'codereviewmanager.cs', None
