# The Trac-hacks autoinstaller

# Table format
# hacks (id, name, type, current, installed, readme, install)

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.web.chrome import ITemplateProvider, add_stylesheet
from webadmin.web_ui import IAdminPageProvider
from db_default import default_table
import re

__all__ = ['HackInstallPlugin']

class HackInstallPlugin(Component):
    """A component managing plugin installation."""
    
    implements(IEnvironmentSetupParticipant, ITemplateProvider, IAdminPageProvider)
    
    def __init__(self):
        """Perform basic initializations."""
        self.url = self.config.get('hackinstall','url',default='http://trac-hacks.org')
        self.svn_url = self.config.get('hackinstall','svn_url',default=self.url+'/svn')
        self.version = self.config.get('hackinstall','version')
        if not self.version:
            import trac
            md = re.match('(\d+\.\d+)',trac.__version__)
            if md:
                self.version = md.group(1)
            else:
                raise TracError, 'HackInstall is unable to determine what version of Trac you are using, please manually configure it.'
 
    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('hacks', 'Trac-Hacks', 'general', 'General')
            yield ('hacks', 'Trac-Hacks', 'plugin', 'Plugins')
            yield ('hacks', 'Trac-Hacks', 'macro', 'Macros')
            
    def process_admin_request(self, req, cat, page, path_info):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        plugins = []
        macros = []
        
        cursor.execute('SELECT id, name, current, installed FROM hacks WHERE type = %s', ('plugin',))
        for row in cursor:
            plugins.append({'id': row[0], 'name': row[1], 'current': row[2], 'installed': row[3]})
        cursor.execute('SELECT id, name, current, installed FROM hacks WHERE type = %s', ('macro',))
        for row in cursor:
            macros.append({'id': row[0], 'name': row[1], 'current': row[2], 'installed': row[3]})
        
        req.hdf['hackinstall'] = { 'version': self.version, 'url': self.url }
        req.hdf['hackinstall.plugins'] = plugins
        req.hdf['hackinstall.macros'] = macros
        
        template = { 'general': 'hackinstall_admin.cs', 'plugin': 'hackinstall_admin_plugin.cs', 'macro': 'hackinstall_admin_macro.cs' }[page]
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
        cursor = db.cursor()
        for sql in db.to_sql(default_table):
            cursor.execute(sql)
        db.commit()   

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

    # Internal methods
    def _install_plugin(self, name):
        pass

    def _download_hack(self, name, type):
        pass
