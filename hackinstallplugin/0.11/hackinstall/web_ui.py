# The Trac-hacks autoinstaller

# Table format
# hacks (id, name, current, decription, deps)

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.perm import IPermissionRequestor
from webadmin.web_ui import IAdminPageProvider
from db_default import default_hacks_table
from core import *
import urlparse, xmlrpclib, re, os

__all__ = ['HackInstallPlugin']

def add_userpass_to_url(url, user=None, password=None):
    """Given a URL, add login data."""
    parts = list(urlparse.urlsplit(url))
    if user:
        if password:
            user = user + ':' + password
        parts[1] = user + '@' + parts[1]
    return urlparse.urlunsplit(parts)

class HackInstallPlugin(Component):
    """A component managing plugin installation."""
    
    implements(IEnvironmentSetupParticipant, ITemplateProvider, IAdminPageProvider, IPermissionRequestor)
    
    def __init__(self):
        """Perform basic initializations."""
        url = self.config.get('hackinstall','url',default='http://trac-hacks.org')
        builddir = self.config.get('hackinstall','builddir')
        version = self.config.get('hackinstall','version')
        self.installer = HackInstaller(self.env, url, builddir, version)
        self.rpc_url = add_userpass_to_url(url+'/login/xmlrpc','TracHacks')
        self.override_version = int(version != '')

    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('HACK_ADMIN'):
            yield ('hacks', 'Trac-Hacks', 'general', 'General')
            yield ('hacks', 'Trac-Hacks', 'plugins', 'Plugins')
            #yield ('hacks', 'Trac-Hacks', 'macros', 'Macros')
            
    def process_admin_request(self, req, cat, page, path_info):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        self.plugins = self._get_hacks('plugin')
        self.macros = self._get_hacks('macro')
        self.updates = self._pending_updates()
        
        if req.method == 'POST':
            if page == 'general':
                if 'save_settings' in req.args:
                    changes = False
                    # Process the URL field
                    if req.args.get('url') != self.installer.url:
                        self.config.set('hackinstall','url', req.args.get('url'))
                        changes = True
                        
                    # Process the version fields
                    if 'override_version' in req.args:
                        self.config.set('hackinstall','version', req.args.get('version'))
                        changes = True
                    elif self.override_version:
                        self.config.remove('hackinstall','version')
                        changes = True
                        
                    # Write back if there were changes
                    if changes:
                        self.config.save()
                    
                        # Reload the new settings
                        self.__init__._original(self)
                                        
                elif 'update_metadata' in req.args:
                    # Update metadata cache
                    self._check_version()
                    self._update('plugin')
                    
                elif 'update_all' in req.args:
                    # Perform all pending updates
                    self._install_plugins(*self.updates['plugins'].keys())
                    
                elif 'update_selected' in req.args:
                    # Only update selected
                    selected = [x[9:] for x in req.args.keys() if x.startswith('doupdate_')]
                    if selected:
                        self._install_plugins(*selected)
                        
            elif page == 'plugins':
                installs = [k[8:] for k in req.args.keys() if k.startswith('install_')]
                if installs:
                    hack = installs[0]
                    req.hdf['hackinstall.message'] = "Installing plugin %s" % (hack)
                    self._install_plugins(hack)

        req.hdf['hackinstall'] = { 'version': self.installer.version, 'override_version': self.override_version, 'url': self.installer.url }
        req.hdf['hackinstall.plugins'] = self.plugins
        req.hdf['hackinstall.updates'] = self.updates
        req.hdf['hackinstall.macros'] = self.macros
        for x in ['general', 'plugins', 'macros']:
            req.hdf['hackinstall.hdf.'+x] = self.env.href.admin(cat,x)
        
        template = { 'general': 'hackinstall_admin.cs', 'plugins': 'hackinstall_admin_plugin.cs', 'macros': 'hackinstall_admin_macro.cs' }[page]
        return template, None

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        self.upgrade_environment(self.env.get_db_cnx())
        
    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        try:
            cursor.execute("SELECT * FROM hacks")
            return False
        except: # Is there some way to only catch DatabaseErrors?
            return True
        
    def upgrade_environment(self, db):
        # 0.10 compatibility hack (thanks Alec)
        try:
            from trac.db import DatabaseManager
            db_manager, _ = DatabaseManager(self.env)._get_connector()
        except ImportError:
            db_manager = db
    
        # Insert the default table
        cursor = db.cursor()
        for sql in db_manager.to_sql(default_hacks_table):
            self.log.debug(sql)
            cursor.execute(sql)
        db.commit()
        
        # Grab initial metadata
        for type in self.installer.valid_types:
            self._update(type)

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """
        Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        from pkg_resources import resource_filename
        return [('hackinstall', resource_filename(__name__, 'htdocs'))]
        
    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ['HACK_ADMIN']

    # Internal methods
    def _get_hacks(self, type):
        # Build hash of name -> installed-rev
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT distname, name FROM hacks WHERE distname NOTNULL')
        distnamemap = dict(cursor)
        
        installed = {}
        if type == 'plugin':
            for f in os.listdir(self.env.path+'/plugins'):
                self.log.debug("Found egg '%s'"%f)
                md = re.match('([^-]+)-([^-]+)-',f)
                if md:
                    plugin = distnamemap.get(md.group(1),md.group(1)+'plugin').lower()
                    md2 = re.search('r(\d+)',md.group(2))
                    if md2:
                        installed[plugin] = int(md2.group(1))
                    else:
                        installed[plugin] = 0
                    self.log.debug('Extracted version = %s'%installed[plugin])
        elif type == 'macro':
            pass # Haven't gotten here yet
    
        # Build the rest of the data structure from the DB
        hacks = {}
        cursor.execute("SELECT id, name, current, description, deps FROM hacks WHERE name LIKE '%%%s'"%type.title())
        for row in cursor:
            hacks[row[1]] = {'id': row[0], 'current': int(row[2]), 'installed': installed.get(row[1].lower(), -1), 'description': row[3], 'deps': row[4], 'lowername': row[1].lower()}
        return hacks
        
    def _get_types(self):
        """Get all known hack types."""
        server = xmlrpclib.ServerProxy(self.rpc_url)
        return server.trachacks.getTypes()
        
    def _check_version(self):
        """Verify that we have a valid version of Trac."""
        server = xmlrpclib.ServerProxy(self.rpc_url)
        versions = server.trachacks.getReleases()
        if self.installer.version not in versions:
            raise TracError, "Trac-Hacks doesn't know about your version of Trac (%s)" % (self.version)
        return True
          
    def _update(self, type):
        """Update metadata from trac-hacks."""
        server = xmlrpclib.ServerProxy(self.rpc_url)

        # Verify this is a valid type
        types = server.trachacks.getTypes()
        if type not in types:
            raise TracError, "Trac-Hacks doesn't know about '%s' hacks" % (type)
        
        # Update metadata
        hacks = server.trachacks.getHacks(self.installer.version, type)
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        for hack in hacks:
            # Grad details for this hack
            details = server.trachacks.getDetails(hack[0])
            self.log.debug("Details for %s: '%s'" % (hack[0], repr(details)))
            deps = ','.join(details['dependencies'])
        
            # Insert/update the DB entry
            cursor.execute("SELECT id FROM hacks WHERE name = %s", (hack[0],))
            row = cursor.fetchone()
            if row:        
                cursor.execute("UPDATE hacks SET current = %s, description = %s, deps = %s WHERE name = %s", (hack[1], details['description'], deps, hack[0]))
            else:
                cursor.execute("INSERT INTO hacks (name, current, description, deps) VALUES (%s, %s, %s, %s)", (hack[0], hack[1], details['description'], deps))
        db.commit()                
            
    def _pending_updates(self):
        """Find what hacks need updating."""
        updates = {'plugins': {}}
        
        # Search for plugins that need updates
        for hack, params in self.plugins.iteritems():
            if params['current'] > 0 and params['installed'] >= 0 and params['current'] > params['installed']:
                updates['plugins'][hack] = params
                
        return updates

    def _install_plugins(self, *plugins):
        """Install the most recent version of a list of hacks."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        for plugin in plugins:
            install_ok, ret = self.installer.install_plugin(plugin, self.plugins[plugin]['current'], self.plugins[plugin]['installed']==-1)
            if install_ok:
                distname = ret[0]
                cursor.execute('UPDATE hacks SET distname = %s WHERE name = %s',(distname,plugin))
            else:
                self.log.warning("Encountered an unknown error when installing %s. Please see your webserver's logs for more information."%plugin)
                raise TracError, "Error during installation, please see the log for more information."
        db.commit()

        # Recompute all of this, so the next page view will be correct
        self.plugins = self._get_hacks('plugin')
        self.updates = self._pending_updates()
