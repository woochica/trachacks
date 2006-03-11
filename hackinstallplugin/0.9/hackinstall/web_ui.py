# The Trac-hacks autoinstaller

# Table format
# hacks (id, name, type, current, installed, readme, install)

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.web.chrome import ITemplateProvider, add_stylesheet
from webadmin.web_ui import IAdminPageProvider
from db_default import default_table
import os, re, xmlrpclib, urlparse, urllib2, zipfile

__all__ = ['HackInstallPlugin']

class HackInstallPlugin(Component):
    """A component managing plugin installation."""
    
    implements(IEnvironmentSetupParticipant, ITemplateProvider, IAdminPageProvider)
    
    def __init__(self):
        """Perform basic initializations."""
        self.url = self.config.get('hackinstall','url',default='https://trac-hacks.org')
        self.builddir = self.config.get('hackinstall','builddir',default=os.environ['PYTHON_EGG_CACHE'])
        self.version = self.config.get('hackinstall','version')
        if not self.version:
            import trac
            md = re.match('(\d+\.\d+)',trac.__version__)
            if md:
                self.version = md.group(1)
            else:
                raise TracError, 'HackInstall is unable to determine what version of Trac you are using, please manually configure it.'
        self.username = self.config.get('hackinstall','username',default='').strip()
        self.password = self.config.get('hackinstall','password',default='').strip()
        
        # Figure out the XML-RPC URL
        if self.username == None:
            self.rpc_url = self.url + '/xmlrpc'
        else:
            urlparts = list(urlparse.urlsplit(self.url))
            urlparts[1] = '%s:%s@%s' % (self.username, self.password, urlparts[1])
            self.rpc_url = urlparse.urlunsplit(urlparts) + '/login/xmlrpc'

    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('TRAC_ADMIN') or True:
            yield ('hacks', 'Trac-Hacks', 'general', 'General')
            yield ('hacks', 'Trac-Hacks', 'plugins', 'Plugins')
            yield ('hacks', 'Trac-Hacks', 'macros', 'Macros')
            
    def process_admin_request(self, req, cat, page, path_info):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        self.plugins = self._get_hacks('plugin')
        self.macros = self._get_hacks('macro')        
        
        if req.method == 'POST':
            if page == 'general':
                if 'update' in req.args:
                    self._check_version()
                    self._update('plugin')
            elif page == 'plugins':
                installs = [k[8:] for k in req.args.keys() if k.startswith('install_')]
                if installs:
                    req.hdf['hackinstall.message'] = "Installing plugin %s" % (installs[0])
                    self._install_hack(installs[0])
                downloads = [k[9:] for k in req.args.keys() if k.startswith('download_')]
                if downloads:
                    self._download_hack(downloads[0])
                    self._build_plugin(downloads[0])

        req.hdf['hackinstall'] = { 'version': self.version, 'url': self.url }
        req.hdf['hackinstall.plugins'] = self.plugins
        req.hdf['hackinstall.macros'] = self.macros
        for x in ['general', 'plugins', 'macros']:
            req.hdf['hackinstall.hdf.%s'%x] = self.env.href.admin('hacks',x)
        
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
        cursor = db.cursor()
        for sql in db.to_sql(default_table):
            self.log.debug(sql)
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
    def _install_hack(self, name):
        """Install a given hack."""
        self._download_hack(name)
        if name.lower().endswith('plugin'):
            self._build_plugin(name)
            self._install_plugin(name)
        self._clean_hack(name)
    
    def _build_plugin(self, name):
        """Create the egg files for a plugin."""
        oldcwd = os.getcwd()
        os.chdir(os.path.join(self.builddir,name.lower(),self.version))
        os.system('python setup.py bdist_egg')
        os.chdir(oldcwd)
        
    def _install_plugin(self, name):
        """Install a plugin into the envrionment's plugin directory."""
        fromdir = os.path.join(self.builddir,name.lower(),self.version,'dist')
        todir = os.path.join(self.env.path,'plugins')
        for d in os.listdir(fromdir):
            if d.endswith('.egg'):
                os.rename(os.path.join(fromdir,d),os.path.join(todir,d))
        self.config.set('components',name.lower()+'.*','disabled')
        self.config.save()

    def _download_hack(self, name):
        """Download and unzip a hack."""
        url = '%s/download/%s.zip' % (self.url,name.lower())
        filename = '%s/%s.zip' % (self.builddir, name.lower())
        self.log.debug('Downloading %s from %s to %s' % (name, url, filename))
        urlf = urllib2.urlopen(url)
        f = open(filename,'w+')
        f.write(urlf.read())
        f.seek(0)
        self.log.debug('Unzipping %s' % filename)
        zip = zipfile.ZipFile(f,'r')
        for zipped in zip.namelist():
            self.log.debug("Archive path is '%s'" % zipped)
            zippedpath = os.path.join(self.builddir,zipped)
            self.log.debug("FS path is '%s'" % zippedpath)
            if not os.path.exists(os.path.dirname(zippedpath)):
                self.log.debug("Trying to make directory '%s'" % os.path.dirname(zippedpath))
                os.makedirs(os.path.dirname(zippedpath))
            if os.path.basename(zippedpath):
                self.log.debug("Writting file")
                zippedf = open(zippedpath, 'w')
                zippedf.write(zip.read(zipped))

    def _clean_hack(self, name):
        """Remove all intermediary files used during installation."""

    def _get_hacks(self, type):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        hacks = {}
        cursor.execute('SELECT id, name, current FROM hacks WHERE type = %s', (type,))
        for row in cursor:
            hacks[row[1]] = {'id': row[0], 'current': row[2]}
        return hacks
        
    def _check_version(self):
        """Verify that we have a valid version of Trac."""
        server = xmlrpclib.ServerProxy(self.rpc_url)
        versions = server.trachacks.getReleases()
        if self.version not in versions:
            raise TracError, "Trac-Hacks doesn't know about your version of Trac (%s)" % (self.version)
        return True
          
    def _update(self, type):
        """Update metadata from trac-hacks."""
        server = xmlrpclib.ServerProxy(self.rpc_url)
        types = server.trachacks.getTypes()
        if type not in types:
            raise TracError, "Trac-Hacks doesn't know about '%s' hacks" % (type)
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        hacks = server.trachacks.getHacks(self.version, type)
        for hack in hacks:
            cursor.execute("SELECT id FROM hacks WHERE name = %s", (hack[0],))
            row = cursor.fetchone()
            if row:        
                cursor.execute("UPDATE hacks SET current = %s WHERE name = %s", (hack[1], hack[0]))
            else:
                cursor.execute("INSERT INTO hacks (name, type, current) VALUES (%s, %s, %s)", (hack[0], type, hack[1]))
        db.commit()                
            
