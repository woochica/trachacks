from trac.core import *
from trac.mimeview.api import IContentConverter, Context
from trac.util.html import Markup
from trac.wiki.formatter import Formatter 
from StringIO import StringIO
from tempfile import mkdtemp, mkstemp
from urllib import urlretrieve
import re
import os
import glob
import zipfile
import base64
import subprocess





class PageToDocPlugin(Component):
    """Convert Wiki pages to filtered HTML for import to MS Word."""
    implements(IContentConverter)
    
    tempdir = ''
    images = []
    imagesubdir = 'img/'
    logsubdir = 'log/'
    img_max_x = '0'
    img_max_y = '0'
    dpi = '96'
    cm2inch = 2.54
    
    verbose = False

    # IContentConverter methods
    def get_supported_conversions(self):
        yield ('zip', 'MS Word', 'zip', 'text/x-trac-wiki', 'application/zip', 7)


    def convert_content(self, req, input_type, source, output_type):
        
        # get parameters from trac ini file
        self.img_max_x = self.env.config.get('pagetodoc', 'img_max_x', self.img_max_x)
        self.img_max_y = self.env.config.get('pagetodoc', 'img_max_y', self.img_max_y)
        self.img_max_y = self.env.config.get('pagetodoc', 'dpi', self.dpi)
        
        # XSL-Transformation        
        xsltfilepath = self.env.config.get('pagetodoc', 'xsltfile', '')
        # TBD: Fehler ausgeben, wenn xsltfile nicht gelesen werden kann
        # TBD: Parameter aus der trac.ini an zentraler Stelle auslesen
        if False:
            if xsltfilepath == '':
                pass
        
        # maybe for later use
        #codepage = self.env.config.get('trac', 'charset', 'iso-8859-1')
        codepage = 'iso-8859-1'
        
        # Convert Wiki markup to HTML, new style
        out = StringIO()
        context = Context.from_request(req, 'wiki', req.path_info[6:])
        Formatter(self.env, context).format(source, out)
        html = Markup(out.getvalue()).encode(codepage, 'replace')
        
        # remove the bad HTML produced by the breadcrumbs plugin
        # RFE: find a universal way to do this
        html = re.compile('(<lh[^>]*>)').sub('', html)
        
        # temporary files and folders
        self.tempdir = mkdtemp(prefix="page2doc")
        htmlfilehandle, htmlfilepath = mkstemp(prefix='trac_', dir=self.tempdir)
        wordfilehandle, wordfilepath = mkstemp(prefix='word_', dir=self.tempdir)
        os.close(wordfilehandle)
        zipfilepath = os.path.join(self.tempdir, os.path.basename(str(req.path_info) + '.zip'))
        
        # for debug: set all rights
        #self.chmod_tmp_dir(self.tempdir)
        
        # images
        # replace href with absolute path and if existing, base auth login
        try:
            login = base64.b64decode(req.environ['HTTP_AUTHORIZATION'][6:]) + '@'      
        except (KeyError, TypeError):
            login = ''
        html = re.sub('<img src="(?!\w+://)', '<img src="%s://%s%s:%d' % (req.scheme, login, req.server_name, req.server_port), html)
        
        # save images to disk
        html = re.sub('<img src="([^"]*)"', self.download_image, html)
               
        # write HTML page to disk
        os.write(htmlfilehandle, '<html><body>' + html + '</body></html>')
        os.close(htmlfilehandle)
        
        # clean up the HTML page using HTML Tidy
        args = '-m -asxhtml -latin1 --doctype omit'
        cmd = 'tidy %s %s' % (args, htmlfilepath)
        self.execute_external_program(cmd)
        
        # workaround namespace
        self.perform_workarounds(htmlfilepath, 'html')
    
        if self.verbose:
            verb = '-v'
        else:
            verb = ''
        cmd = 'xsltproc %s -o %s %s %s' % (verb, wordfilepath, xsltfilepath, htmlfilepath)
        self.execute_external_program(cmd)
        
        # workaround pre-tags
        self.perform_workarounds(wordfilepath, 'pre')
        
        
        # create a zip file and store all files into it      
        zipfilehandle = zipfile.ZipFile(zipfilepath, "w")
        zipfilehandle.write(wordfilepath, os.path.basename(str(req.path_info) + '.htm'))       
        for image in self.images:
            zipfilehandle.write(image, self.imagesubdir + os.path.basename(image))     
        zipfilehandle.close()
        zip_file = open(zipfilepath, "rb")
        zip = zip_file.read()
        zip_file.close()
        
        # delete temporary folders and files
        self.remove_dir(os.path.join(self.tempdir, self.logsubdir))
        self.remove_dir(os.path.join(self.tempdir, self.imagesubdir))
        self.remove_dir(self.tempdir)
        
        # reset image list
        self.images = []
         
        return (zip, 'application/zip')
    
    
    def execute_external_program(self, command):
        logdir = os.path.join(self.tempdir, self.logsubdir)
        self.create_dir(logdir)
        
        # Create output and error log files
        outptr, outFile = mkstemp(dir=logdir)
        errptr, errFile = mkstemp(dir=logdir)
    
        # Call the subprocess using convenience method
        retval = subprocess.call(command, shell=True, stderr=errptr, stdout=outptr)
        os.close(outptr)
        os.close(errptr)
                
        # read stdout and stderr
        # its strange that all output goes to stderr instead of stdout, in both cases (error and no error)
        # so always use stderr    
        errptr = file(errFile, "r")
        errData = errptr.read()
        errptr.close()
        
        # log to trac.log
        if self.verbose:
            self.env.log.info('--------- EXTERNAL PROGRAM OUTPUT, command is ' + command)
            self.env.log.info(errData)
        
        # not needed right now
        #outptr = file(outFile, "r")
        #outData = outptr.read()
        #outptr.close()
        
        # Check the process exit code
        if retval > 1:
            raise Exception("Error executing command (return code = %s): %s" % (retval, errData))          
   
    # remove the xml namespace from the file
    # to be removed once I find out how to override this 
    def perform_workarounds(self, htmlfilepath, which=''):
         # Workaround: Entferne die Namespace-Angabe in der HTML-Datei
        htmlfilehandle = open(htmlfilepath, "r")
        html = htmlfilehandle.read()
        htmlfilehandle.close()
        
        # replace namespace
        if which == 'html':
            html = re.sub('(<html xmlns="http://www.w3.org/1999/xhtml">)', '<html>', html)
        
        # remove line feeds in <pre>-tags    
        if which == 'pre':
            html = re.sub(r'<pre[^>]*>\n([^<]*)</pre>', self.remove_line_feeds, html)
        
        htmlfilehandle = open(htmlfilepath, "w")
        htmlfilehandle.write(html)
        htmlfilehandle.close()
        
    def remove_line_feeds(self, matchObj):
        return '<pre>' + re.sub(r'\n', '<br />', matchObj.group(1)) + '<br /></pre>'
    

    def download_image(self, matchObj):
        imgdir = os.path.join(self.tempdir, self.imagesubdir)
        
        # create path to imagedir, if not existing
        self.create_dir(imgdir)
        
        # save image to disk
        (filename, fileext) = os.path.splitext(os.path.basename(matchObj.group(1)))
        # remove any trailing GET-Parameters from the file extension e.g. '.jpg?format=raw')
        # fileext = fileext[:fileext.find('?')]
        
        # line above does not work due to encoding issues ('?' is something like '%3f' then)
        # therefore just remove the file extention, and let ImageMagick detect the file type by itself
        # this has been tested with ImageMagick 6.4.2 and PNG, JPG, TIFF and GIF files
        fileext = ''
        
        # create temporary file 
        fh, fn = mkstemp(prefix=filename, suffix=fileext, dir=imgdir)
        os.close(fh)
        urlretrieve(matchObj.group(1), fn) 
        
        # resize images, if wanted, using ImageMagick
        if int(self.img_max_x)/self.cm2inch*int(self.dpi) > 0 and int(self.img_max_y)/self.cm2inch*int(self.dpi) > 0:
            #args = "-density %sd -resize '%sx%s>'" % (self.dpi, self.img_max_x, self.img_max_y)
            args = "-resize '%sx%s>' -resample %s" % (self.img_max_x, self.img_max_y, self.dpi)
            
            cmd = 'convert %s %s %s' % (fn, args, fn)
            self.execute_external_program(cmd)
        
        # add image to image list
        self.images.append(fn)
        
        return '<img src="%s"' % (self.imagesubdir + os.path.basename(fn))
    
    # for debugging
    def chmod_tmp_dir(self, tempdir):
        os.chmod(tempdir, 0777)
        
        # files
        for f in glob.glob(os.path.join(tempdir ,"*")):
            os.chmod(f, 0777)
    
    # directory functions        
    def create_dir(self, dir):
        if not os.path.isdir(dir):
            os.mkdir(dir)
       
    def remove_dir(self, dir):
        if os.path.isdir(dir):
            for f in glob.glob(os.path.join(dir, '*')):
                os.unlink(f)
            os.rmdir(dir)
            
        
        

    
    
