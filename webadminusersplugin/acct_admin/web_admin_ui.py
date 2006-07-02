import sets

from trac.core import *
from trac.web.chrome import ITemplateProvider

from acct_mgr.api import AccountManager

from webadmin.web_ui import IAdminPageProvider


class UserManager(Component):
    """Allows admins to add and remove users.
    """
    implements(IAdminPageProvider, ITemplateProvider)

    #IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('general', 'General', 'users', 'User Accounts')

    def process_admin_request(self, req, category, page, path_info):
        mgr = AccountManager(self.env)
        if path_info:
            return self._process_user_request(req, category, page, 
                                              path_info, mgr)
        else:
            if req.method == 'POST':
                if req.args.get('add'):
                    self._do_add(req, mgr)
                elif req.args.get('remove'):
                    self._do_remove(req, mgr)
        # run user list through a set to work around a bug in
        # account manager
        # see http://trac-hacks.org/ticket/180
        users = list(sets.Set(mgr.get_users()))
        users.sort()
        req.hdf['admin.users'] = \
            [{'name': u, 
              'key': u, 
              'href': self.env.href.admin(category, page, u)
             } for u in users]
        return 'admin_users.cs', None

    def _process_user_request(self, req, cat, page, user, mgr):
        if not mgr.has_user(user):
            req.redirect(self.env.href.admin(cat, page))
            return

        success = False
        if req.method == 'POST':
            if req.method == 'POST':
                if req.args.get('change'):
                    success = self._do_change(req, mgr, user)
                elif req.args.get('delete'):
                    success = self._do_delete(req, mgr, user)
                else:
                    success = True
        if success:
            req.redirect(self.env.href.admin(cat, page))
        else:
            req.hdf['admin.user'] = user
            return 'admin_user.cs', None

    def _do_add(self, req, mgr):
        user = req.args.get('username')
        password = req.args.get('password1')
        if mgr.has_user(user):
            error = 'An account with that name already exists.'
            req.hdf['users.error'] = error
        elif len(password) == 0:
            req.hdf['users.error'] = 'Password cannot be empty.'
        elif password != req.args.get('password2'):
            req.hdf['users.error'] = 'The passwords must match.'
        else:
            mgr.set_password(user, password)

    def _do_remove(self, req, mgr):
        sel = req.args.get('sel')
        sel = isinstance(sel, list) and sel or [sel]
        for key in sel:
            if mgr.has_user(key):
                mgr.delete_user(key)

    def _do_delete(self, req, mgr, user):
        if mgr.has_user(user):
            mgr.delete_user(user)
            return True

    def _do_change(self, req, mgr, user):
        password = req.args.get('password1')
        if len(password) == 0:
            req.hdf['users.error'] = 'Password cannot be empty.'
        elif password != req.args.get('password2'):
            req.hdf['users.error'] = 'The passwords must match.'
        else:
            mgr.set_password(user, password)
            return True

    #ITemplateProvider methods
    def get_templates_dirs(self):
		from pkg_resources import resource_filename
		return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return []
