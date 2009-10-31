import os
from StringIO import StringIO

from trac.core import *
from trac.config import *
from trac.admin.api import IAdminPanelProvider
from trac.web.chrome import add_stylesheet, add_script, add_notice, add_warning, ITemplateProvider
#from trac.util import get_reporter_id
from trac.util.html import html
from trac.util.datefmt import format_datetime
from trac.util.translation import _
from trac.env import Environment
from trac.perm import PermissionError

from tracusersync.api import UserSyncAdmin

#__all__=['IUserManagerPanelProvider']

class UserSyncAdminPage(Component):

    implements(IAdminPanelProvider, ITemplateProvider)

    def __init__(self):
        self.api = UserSyncAdmin(self.env)

    # panel_providers = ExtensionPoint(IUserManagerPanelProvider)
    # cells_providers = ExtensionPoint(IUserListCellContributor)
    
    default_panel = Option('user_manager', 'admin_default_panel', 'profile',
        """Default user admin panel.""")

    # Configuration options.
    _users_keep = ListOption('user_sync', 'users_keep', '',
      doc = 'Comma separated list of users to keep under all circumstances when'
      ' purging. All your permission groups will be added automatically.')
    _merge_conflicts = Option('user_sync', 'merge_conflicts', 'skip',
      doc = 'What should be done when two field values conflict with each other?'
      ' Valid settings are: "skip" (default: do not sync this user) and "newer"'
      ' (take values from the newer record, i.e. the environment the user was'
      ' last active in). Note that the latter does not necessarily have the more'
      ' recent data, as it only stands for the last login, not the last change.')
    _sync_fields = ListOption('user_sync', 'sync_fields', 'email,name',
      doc = 'Comma separated List of fields to be synced. The default is'
      ' "email,name" and includes the two fields used by the !AccountManagerPlugin.'
      ' If you are additionally using the !UserManagerPlugin, you may have to'
      ' add the fields you enabled there as well.')
    _sql_file_path = Option('user_sync','sql_file_path','',
      doc = 'Path to the directory of the file, where update statements should be'
      ' saved into. If empty (default), the log directory of the executing trac'
      ' environment will be taken.')
    _dryrun = BoolOption('user_sync','dryrun','true',
      doc = 'Stay read-only (true) or really apply the changes (false). As long'
      ' as this plugin is in early-beta state, it defaults to "true" (read-only).')

    # IAdminPageProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('accounts', _('Accounts'), 'usersync', 'User Sync')
            #yield ('accounts', _('Accounts'), 'users', 'Users')
        
    def render_admin_panel( self, req, cat, page, path_info):
        # here comes the page content, handling, etc.
        error = TracError('')
        parentdir = os.getenv('TRAC_ENV_PARENT_DIR')
        self.env.log.debug('TRAC_ENV_PARENT_DIR found: %s' % (parentdir,))

        self.data = {}
        self.data['err'] = []
        self.data['msg'] = []
        self.data['log'] = []
        data = {}

        # if we don't have a parentdir, we are useless
        if parentdir:
           # find all trac environments
           tracenvs = self.api.get_envs(parentdir)

           # read users from password file
           #config.get(section,key,default)
           pwdfile = self.env.config.get('account-manager','password_file')
           if pwdfile and os.path.exists(pwdfile):
              self.env.log.debug('Using password file "%s"' % (pwdfile,))
              self.users = self.api.get_pwd_users(pwdfile)
              if not self.users:
                 self.data['err'].append('No users found in the password file "%s", aborting.' % (pwdfile,))

           else:
              self.env.log.debug('No password file found')
              if pwdfile:
                 self.data['err'].append('The configured password file "%s" was not found, aborting.' % (pwdfile,))
              else:
                 self.data['err'].append('You have no password file (password_file = /path/to/.htpasswd) configured in the [account-manager] section of your trac.ini. Aborting.')

        else:
           self.data['err'].append('TRAC_ENV_PARENT_DIR is not defined - so we cannot do anything!')

        # Made it here - so we have all data to set up the WebIf:
        if len(self.data['err'])<1:
           data['tracenvs'] = tracenvs
           data['pwdfile']  = pwdfile
           # data['users'] is just for debug on display - can be dropped later
           data['users']    = self.users
           # users_keep will be needed for purging once that is implemented
           #data['users_keep'] = ','.join(self.api.get_perm_groups(self.env.path))

           # Form sent? Process!
           if req.method=="POST":
              message = self._do_process(req,tracenvs)

        # append the messages
        data['us_message'] = self.data['msg']
        data['us_error']   = self.data['err']
        data['us_log']     = self.data['log']

        # adding stylesheets
        add_stylesheet(req, 'tracusersync/css/admin_us.css')
        add_script(req, 'tracusersync/js/admin_us.js')
        
        return 'sync.html', data

    # ITemplateProvider
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        return [('tracusersync', resource_filename(__name__, 'htdocs'))] 
        #return []

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver/Genshi templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]


    # Internal methods
    def _do_process(self, req, tracenvs):
        """Process form data received via POST
        @param req      : the request
        @param tracenvs : trac environments as returned by _get_envs
        """
        self.env.log.debug('Processing form data')
        syncok  = True
        purgeok = True
        if req.args.get('action_sync'):
           syncok = self._do_sync(req,tracenvs)
        if req.args.get('action_purge'):
           purgeok = self._do_purge()
        return syncok and purgeok

    def _do_sync(self, req, tracenvs):
        """Synchronize user data between the environments
        @param req      : the request
        @param tracenvs : trac environments as returned by _get_envs
        """
        
        # Check whether we have all required information
        envs = req.args.getlist('tracenv')
        le = len(envs)
        self.env.log.debug('UserSync: %s environments to synchronize' % (le,))
        if len(envs)<2:
           self.data['err'].append('For a synchronization, you must select at least 2 environments. You only selected: %s' % (', '.join(envs)))
           return False

        self.data['log'].append('Users from password file: %s ' % (', '.join(self.users)))

        # Fetching account data from the environments
        self.data['log'].append('Fetching user data from environments...')
        self.env.log.debug('TracEnvs: %s' % (tracenvs,))
        userlist = "'"+"','".join(self.users)+"'"
        data = {}
        rec_err = {}
        attr = "'name','email','email_verification_sent_to','email_verification_token'"
        for tracenv in tracenvs:
           try:
             recs = self.api.get_tracenv_userdata(req,os.path.join(os.getenv('TRAC_ENV_PARENT_DIR'),tracenv),userlist)
           except PermissionError:
             self.data['log'].append('You do not have the required permissions in %s - excluding it from synchronization' % (tracenv,))
             self.env.log.info('Sorry, but you do not have the required permissions in %s' % (tracenv,))
             continue
           # each env must at least have one user (the TRAC_ADMIN). No records returned here means an error (different password file or missing privs)
           if not recs:
             del tracenvs[tracenvs.index(tracenv)]
             self.data['log'].append('Environment %s uses a different password file - excluding it from synchronization' % (tracenv,))
             continue
           ucnt = 0
           for sid in recs:
             if not sid in data: data[sid] = []
             data[sid].append(recs[sid])
             ucnt += 1
           self.env.log.debug('* %i relevant records' % (ucnt,))
           self.data['log'].append('%i relevant records in %s' % (ucnt,tracenv,))

        # Merging data
        res, err = self.api.merge(data)
        self.env.log.debug('%i merged records, %i records skipped' % (len(res),len(err)))
        self.data['log'].append('Merged user data: %i unique records, %i records skipped' % (len(res),len(err)))
        if not res:
           self.data['err'].append('Resulting user data collection is empty - nothing to be updated!')
           self.env.log.debug('Resulting user data collection is empty - nothing to be updated!')
           return False
        #self.env.log.info(res)

        # Updating environments
        env_ok = 0
        env_err = 0
        for tracenv in tracenvs:
          success, msg = self.api.update_tracenv_userdata(req, os.path.join(os.getenv('TRAC_ENV_PARENT_DIR'),tracenv), res)
          if success:
            self.data['log'].append(msg)
            env_ok += 1
          else:
            #self.data['msg'].append('Failed to update environment! For details, see log below.')
            self.data['log'].append(msg)
            env_err += 1
        if env_err > 0:
          self.data['err'].append('%i environments had errors on updating. Please see the log below for details.' % (env_err,))
          return False
        else:
          self.data['msg'].append('Users successfully synchronized for %i environments. Please see the log below for details.' % (env_ok,))
          return True

    def _do_purge(self):
      """Purge obsolete data - i.e. environment data (sessions, preferences,
      permissions) from users no longer existing. Wrapper to api.do_purge()
      """
      self.data['log'].append('Purge was requested - but is not yet available, sorry.')
      ok, msg = self.api.do_purge()
      if ok: self.data['msg'].append(msg)
      else: self.data['err'].append(msg)
      return ok

