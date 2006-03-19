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
    
    def __init__(self, env, url, builddir=None, version=None, user=None, password=None):
        self.url = url        
        if not builddir:
            builddir = os.environ['PYTHON_EGG_CACHE']
        self.builddir = builddir
        if not version:
            md = re.match('(\d+\.\d+)',TRAC_VERSION)
            if md:
                version = md.group(1)
            else:
                raise TracError, 'HackInstaller is unable to determine what version of Trac you are using, please manually configure it.'
        self.version = version
        self.env = env
        
    def install_hack(self, name, rev):
        """Install a given hack."""
        if name.lower().endswith('plugin'):
            self.install_plugin(name, rev)
        elif name.lower().endswith('macro'):
            self.download_hack(name, rev)
            self.install_macro(name, rev)
            self.clean_hack(name, rev)
        else:
            raise HackInstallerError, "Unknown hack type for %s"%name
            
    def install_plugin(self, name, rev):
        """Install a plugin into the envrionment's plugin directory."""
        recordf = tempfile.NamedTemporaryFile(suffix='.txt',prefix='hackinstall-record',dir=self.builddir,mode='w')
        command = "easy_install -m --install-dir=%s --record=%s %s/svn/%s/%s" % (self.env.path+'/plugins',recordf.name,self.url,name.lower(),self.version)
        self.env.log.info('Running os.system(%s)'%command)
        os.system(command)
        installed = recordf.readlines()
        recordf.close()
        self.env.log.debug("installed = '%s'" % installed)
        for f in installed:
            f = f.strip()
            self.env.log.debug("Processing file '%s'" % f)
            if f.endswith('.egg'):
                # Extract plugin entry points
                dist = pkg_resources.Distribution.from_filename(f,pkg_resources.EggMetadata(zipimport.zipimporter(f)))
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
                
                # Rename a plugin from Foo-0.5-py2.4.egg to Foo-0.5-rREV-py2.4.egg
                md = re.match('([^-]+-)([^-]+)(-py\d\.\d+\.egg)',f)
                if md:
                    newname = f
                    md2 = re.search('(r\d+)',md.group(2))
                    if md2:
                        newname = re.sub('(.*)(r\d+)(.*)','\1r%s\3'%rev,newname)
                    else:
                        newname = '%s%s_r%s%s' % (md.group(1),md.group(2),rev,md.group(3))
                    self.env.log.debug('Renaming %s to %s' % (f, newname))
                    os.rename(self.env.path+'/plugins/'+f,self.env.path+'/plugins/'+newname)
                    
                # Remove all old versions
                md = re.match('([^-]+)-',f)
                if md:
                    for f2 in os.listdir(self.env.path+'/plugins'):
                        md2 = re.match('([^-]+)-',f2)
                        if md2 and md.group(1) == md2.group(1):
                            os.remove(self.env.path+'/plugins/'+f2)

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

    


