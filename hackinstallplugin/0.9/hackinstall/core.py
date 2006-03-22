# Actual hack installation routines
# These are left as a separate module so that other people can steal them

from trac.core import *
from trac import __version__ as TRAC_VERSION
import os, re, urlparse, urllib2, zipfile, pkg_resources, zipimport, tempfile

__all__ = ['HackInstallerError','HackInstaller']

class HackInstallerError(TracError):
    """An error during installation."""
    pass
    
class HackInstaller(object):
    """A class implementing hack installation logic."""
    
    # Types of hacks I can handle
    valid_types = ['plugin', 'macro']
    
    def __init__(self, env, url, builddir=None, version=None, user=None, password=None):
        self.url = url        
        if not builddir:
            builddir = os.environ.get('PYTHON_EGG_CACHE')
        self.builddir = builddir
        if not version:
            md = re.match('(\d+\.\d+)',TRAC_VERSION)
            if md:
                version = md.group(1)
            else:
                raise TracError, 'HackInstaller is unable to determine what version of Trac you are using, please manually configure it.'
        self.version = version
        self.env = env
        
    def install_hack(self, name, rev, new=False):
        """Install a given hack."""
        self.env.log.info('Installing %s hack.'%name)
        if name.lower().endswith('plugin'):
            return self.install_plugin(name, rev, new)
        elif name.lower().endswith('macro'):
            self.download_hack(name, rev)
            self.install_macro(name, rev)
            self.clean_hack(name, rev)
        else:
            raise HackInstallerError, "Unknown hack type for %s"%name
            
    def install_plugin(self, name, rev, new=False):
        """Install a plugin into the envrionment's plugin directory."""
        plugins_dir = os.path.join(self.env.path,'plugins')
        installed_dists = []
        
        # Use easy_install to build the egg
        temp_file = tempfile.NamedTemporaryFile(suffix='.txt',prefix='hackinstall-record',dir=self.builddir,mode='r')
        command = "easy_install -m --install-dir=%s --record=%s %s/svn/%s/%s" % (plugins_dir, temp_file.name, self.url, name.lower(), self.version)
        self.env.log.info('Running os.system(%s)'%command)
        rv = os.system(command)
        if rv != 0:
            self.env.log.warning("easy_install failed with a return code of %s. Please look in your webserver's error log for the output"%rv)
            return (False, None)
        
        # Retrieve the installed files
        installed = temp_file.readlines()
        temp_file.close()

        # Process each installed file
        for old_file in installed:
            old_file = old_file.strip() # Remove newlines
            self.env.log.debug("Processing file '%s'" % old_file)
            if old_file.endswith('.egg'):
                dist = pkg_resources.Distribution.from_filename(old_file,pkg_resources.EggMetadata(zipimport.zipimporter(old_file)))
                # Find and disable entry points (only on new installs)
                if new:
                    if dist.has_metadata('trac_plugin.txt'):
                        self.env.log.debug('trac_plugin.txt file detected')
                        for line in dist.get_metadata_lines('trac_plugin.txt'):
                            self.env.config.set('components',line.strip()+'.*','disabled')
                    else:
                        self.env.log.debug('Entry point plugin detected')
                        for entry_name in dist.get_entry_map('trac.plugins'):
                            self.env.log.debug("Processing entry name '%s'"%entry_name)
                            entry_point = dist.get_entry_info('trac.plugins', entry_name)
                            self.env.log.debug("Module name is '%s'"%entry_point.module_name)
                            self.env.config.set('components',entry_point.module_name+'.*','disabled')
                    self.env.config.save()

                old_name = os.path.basename(old_file)
                new_name = None
                # Rename a plugin from Foo-0.5-py2.4.egg to Foo-0.5-rREV-py2.4.egg
                md = re.match('([^-]+-)([^-]+)(-py\d\.\d+\.egg)',old_name)
                if md:
                    md2 = re.search('(r\d+)',md.group(2))
                    if md2:
                        new_name = re.sub('(.*)(r\d+)(.*)','\1r%s\3'%rev,old_name)
                    else:
                        new_name = '%s%s_r%s%s' % (md.group(1),md.group(2),rev,md.group(3))
                    new_file = os.path.join(plugins_dir, new_name)
                    self.env.log.debug('Renaming %s to %s' % (old_file, new_file))
                    os.rename(old_file, new_file)
                    
                # Remove all old versions
                md = re.match('([^-]+)-',new_name)
                if md:
                    for plugin_name in os.listdir(plugins_dir):
                        md2 = re.match('([^-]+)-',plugin_name)
                        self.env.log.debug("Removal scan: new_name='%s' plugin_name='%s'" % (new_name,plugin_name))
                        if md2 and new_name != plugin_name and md.group(1) == md2.group(1):
                            plugin_file = os.path.join(plugins_dir,plugin_name)
                            self.env.log.debug('Removing '+plugin_file)
                            os.remove(plugin_file)
                            
                installed_dists.append(dist.project_name)
        return (len(installed_dists)>0, installed_dists)

    def download_hack(self, name, rev):
        """Download and unzip a hack."""
        url = '%s/download/%s.zip' % (self.url,name.lower())
        filename = '%s/%s.zip' % (self.builddir, name.lower())
        self.env.log.debug('Downloading %s from %s to %s' % (name, url, filename))
        urlf = urllib2.urlopen(url)
        f = open(filename,'w+')
        f.write(urlf.read())
        f.seek(0)
        self.env.log.debug('Unzipping %s' % filename)
        zip = zipfile.ZipFile(f,'r')
        for zipped in zip.namelist():
            self.env.log.debug("Archive path is '%s'" % zipped)
            zippedpath = os.path.join(self.builddir,zipped)
            self.env.log.debug("FS path is '%s'" % zippedpath)
            if not os.path.exists(os.path.dirname(zippedpath)):
                self.env.log.debug("Trying to make directory '%s'" % os.path.dirname(zippedpath))
                os.makedirs(os.path.dirname(zippedpath))
            if os.path.basename(zippedpath):
                self.env.log.debug("Writting file")
                zippedf = open(zippedpath, 'w')
                zippedf.write(zip.read(zipped))

    def clean_hack(self, name, rev):
        """Remove all intermediary files used during installation."""
        os.remove(os.path.join(self.builddir,name.lower()+'.zip'))

    


