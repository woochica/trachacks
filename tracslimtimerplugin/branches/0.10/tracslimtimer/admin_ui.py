
from pkg_resources import require, resource_filename, ResolutionError
import datetime
import os

from trac.core import *
from trac.perm import IPermissionRequestor
from trac.web.chrome import add_stylesheet, add_script, ITemplateProvider
from dump_users import ReportDumper
from users import Users

# Import IAdminPanelProvider or IAdminPageProvider depending on if we're trac
# 0.11 or 0.10

try: # Trac 0.11
   from trac.admin import IAdminPanelProvider

except ImportError:
    IAdminPanelProvider = None

    try: # Trac 0.10 with WebAdmin plugin
        require("TracWebAdmin")
        from webadmin.web_ui import IAdminPageProvider
    except (ResolutionError, ImportError):
        IAdminPageProvider = None

###############################################################################
#
# Basic settings panel
#
###############################################################################

class TracSlimTimerBasicPanelProvider(Component):

    implements (IPermissionRequestor, ITemplateProvider)

    if IAdminPanelProvider:
        implements(IAdminPanelProvider)
    elif IAdminPageProvider:
        implements(IAdminPageProvider)

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if req.perm.has_permission('SLIMTIMER_CONFIG'):
            yield ('slimtimer', 'SlimTimer Integration',
                   'slimtimer.basic', 'Basic Settings')

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.assert_permission('SLIMTIMER_CONFIG')

        if req.method == 'POST':
            for option in ('api_key'):
                self.config.set('slimtimer', option, req.args.get(option))
            self.config.save()
            req.redirect(req.href.admin(cat, page))

        api_key = self.config.get('slimtimer', 'api_key')
        add_stylesheet(req, 'slimtimer/css/slimtimer.css')
        return 'config_basics.html', {'api_key': api_key }

    # IAdminPageProvider methods

    get_admin_pages = get_admin_panels

    def process_admin_request(self, req, cat, page, path_info):
        template, data = self.render_admin_panel(req, cat, page, path_info)

        req.hdf['admin.slimtimer'] = data
        return template.replace('.html', '.cs'), None

    def get_admin_pages(self, req):
        return self.get_admin_panels(req)

    def render_admin_page(self, req, cat, page, path_info):
        return self.render_admin_panel(req, cat, page, path_info)

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['SLIMTIMER_CONFIG']

    # ITemplateProvider

    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        return [('slimtimer', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        return [resource_filename(__name__, 'templates')]

###############################################################################
#
# User settings panel
#
###############################################################################

class TracSlimTimerUserPanelProvider(Component):

    if IAdminPanelProvider:
        implements(IAdminPanelProvider)
    elif IAdminPageProvider:
        implements(IAdminPageProvider)

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if req.perm.has_permission('SLIMTIMER_CONFIG'):
            yield ('slimtimer', 'SlimTimer Integration',
                   'slimtimer.user', 'Users')

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.assert_permission('SLIMTIMER_CONFIG')

        config_file = self._get_user_config_file()
        users = Users(config_file)

        if req.method == 'POST':
            if req.args.get('action','') == 'modify':
                self._do_mod_user(req, users)
                req.redirect(req.href.admin(cat, page))

            elif req.args.get('action','') == 'delete':
                self._do_delete_user(req, users)
                req.redirect(req.href.admin(cat, page))

            else:
                self._do_add_user(req, users)
                req.redirect(req.href.admin(cat, page))

        add_stylesheet(req, 'slimtimer/css/slimtimer.css')
        add_script(req, 'slimtimer/js/slimtimer_users.js')
        return 'config_users.html', { 'users': users.get_all_users() }

    # IAdminPageProvider methods

    get_admin_pages = get_admin_panels

    def process_admin_request(self, req, cat, page, path_info):
        template, data = self.render_admin_panel(req, cat, page, path_info)

        req.hdf['admin.slimtimer'] = data
        return template.replace('.html', '.cs'), None

    def get_admin_pages(self, req):
        return self.get_admin_panels(req)

    def render_admin_page(self, req, cat, page, path_info):
        return self.render_admin_panel(req, cat, page, path_info)

    # Internal methods

    def _get_user_config_file(self):
        return os.path.join(self.env.path, 'conf', 'users.xml')

    def _do_add_user(self, req, users):
        trac_username = req.args.get('trac_username', '')
        new_user = users.add_user(trac_username)
        new_user['st_user'] = req.args.get('st_username', '')
        new_user['st_pass'] = req.args.get('st_password', '')
        new_user['default_cc'] = req.args.has_key('default_cc')
        new_user['report'] = req.args.has_key('report')
        users.save()

    def _do_mod_user(self, req, users):
        trac_username = req.args.get('user', '')
        existing_user = users.get_st_user(trac_username)

        # 
        # Check the user already exists
        #
        if not existing_user:
            self.log.error("Couldn't find user to edit: %s" \
                           % trac_username)
            return

        # 
        # If they've changed the trac username we need to update the
        # hashtable in Users
        #
        if trac_username != req.args.get('trac_username',''):
            old = trac_username
            new = req.args.get('trac_username', '')

            #
            # Preserve the old password; it's the only field that might not be
            # set again below
            #
            old_password = existing_user.get('st_pass','')
            existing_user = users.add_user(new)
            existing_user['st_pass'] = old_password
            users.delete_user(old)

        existing_user['st_user'] = req.args.get('st_username', '')

        #
        # Special handling so the admin doesn't need to remember the user's
        # password to change other settings
        #
        new_password = req.args.get('st_password', '')
        if new_password != "__as_before__":
            existing_user['st_pass'] = new_password

        existing_user['default_cc'] = req.args.has_key('default_cc')
        existing_user['report'] = req.args.has_key('report')

        users.save()

    def _do_delete_user(self, req, users):

        trac_username = req.args.get('trac_username')
        if (trac_username):
            users.delete_user(trac_username)
            users.save()

###############################################################################
#
# Report settings panel
#
###############################################################################

class TracSlimTimerReportPanelProvider(Component):

    if IAdminPanelProvider:
        implements(IAdminPanelProvider)
    elif IAdminPageProvider:
        implements(IAdminPageProvider)

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if req.perm.has_permission('SLIMTIMER_CONFIG'):
            yield ('slimtimer', 'SlimTimer Integration',
                   'slimtimer.reporting', 'Reporting')

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.assert_permission('SLIMTIMER_CONFIG')

        if req.method == 'POST':
            if req.args.get('apply'):
                for option in ('db_host', 'db_username', 'db_password',
                               'db_dsn', 'report_log'):
                    self.config.set('slimtimer', option, req.args.get(option))
                self.config.save()
                req.redirect(req.href.admin(cat, page))

            elif req.args.get('dump'):
                ndays = int(req.args.get('days'))
                range_end = datetime.datetime.today()
                range_start = range_end
                range_start -= datetime.timedelta(days=ndays)

                tracbase = self.env.path
                dumper = ReportDumper()
                dumper.dump(tracbase, range_start, range_end)

        data = {
            'host':     self.config.get('slimtimer', 'db_host'),
            'username': self.config.get('slimtimer', 'db_username'),
            'password': self.config.get('slimtimer', 'db_password'),
            'database': self.config.get('slimtimer', 'db_dsn'),
            'report_log': self.config.get('slimtimer', 'report_log'),
            'default_report_log': self.get_default_report_log()
        }
        add_stylesheet(req, 'slimtimer/css/slimtimer.css')
        return 'config_reports.html', data

    # IAdminPageProvider methods

    get_admin_pages = get_admin_panels

    def process_admin_request(self, req, cat, page, path_info):
        template, data = self.render_admin_panel(req, cat, page, path_info)

        req.hdf['admin.slimtimer'] = data
        return template.replace('.html', '.cs'), None

    def get_admin_pages(self, req):
        return self.get_admin_panels(req)

    def render_admin_page(self, req, cat, page, path_info):
        return self.render_admin_panel(req, cat, page, path_info)

    def get_default_report_log(self):
        #
        # This complicated mess allows us to automatically arrive at something
        # like: /var/trac/0.10.3/log/time_report.log
        #
        log_dir = os.path.dirname(self.env.log_file)
        if log_dir:
            (first, second) = os.path.split(log_dir)
            if second == 'httpd':
                log_dir = first
        else:
            log_dir = self.env.get_log_dir()
        return os.path.join(log_dir, 'time_report.log')

