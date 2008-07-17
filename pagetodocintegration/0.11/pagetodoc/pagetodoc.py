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





class PageToDocPlugin(Component):
    """Convert Wiki pages to filtered HTML for import to MS Word."""
    implements(IContentConverter)
    
    tempdir = ''
    images = []
    imagesubdir = 'img/'

    # IContentConverter methods
    def get_supported_conversions(self):
        yield ('zip', 'MS Word', 'zip', 'text/x-trac-wiki', 'application/zip', 7)


    def convert_content(self, req, input_type, source, output_type):      
        
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
        htmlfilehandle, htmlfilepath = mkstemp(dir=self.tempdir)
        wordfilehandle, wordfilepath = mkstemp(dir=self.tempdir)
        zipfilepath = os.path.join(self.tempdir, os.path.basename(str(req.path_info) + '.zip'))
        
        # for debug: set all rights
        #self.chmod_tmp_dir(self.tempdir)
        
        # images
        # replace href with absolute path and if existing, base auth login
        try:
            login = base64.b64decode(req.environ['HTTP_AUTHORIZATION'][6:]) + '@'      
        except KeyError:
            login = ''
        html = re.sub('<img src="(?!\w+://)', '<img src="%s://%s%s:%d' % (req.scheme, login, req.server_name, req.server_port), html)
        
        # save images to disk
        html = re.sub('<img src="([^"]*)"', self.download_image, html)
               
        # write HTML page to disk
        os.write(htmlfilehandle, '<html><body>' + html + '</body></html>')
        os.close(htmlfilehandle)
        
        # clean up the HTML page using HTML Tidy
        # maybe for later use
        #tidy_input_enc = self.env.config.get('pagetodoc', 'input-encoding', 'utf8')
        #tidy_output_enc = self.env.config.get('pagetodoc', 'output-encoding', 'latin1')   
        #args = '-m -asxhtml --doctype omit --input-encoding %s --output-encoding %s' % (tidy_input_enc, tidy_output_enc)
        args = '-m -asxhtml -latin1 --doctype omit'
        cmd = 'tidy %s %s' % (args, htmlfilepath)
        os.system(cmd)
        
        # Workaround
        self.xmlns_workaround(htmlfilepath)
        
        # XSL-Transformation        
        xsltfilepath = self.env.config.get('pagetodoc', 'xsltfile', '')
        cmd = 'xsltproc -o %s %s %s' % (wordfilepath, xsltfilepath, htmlfilepath)
        os.system(cmd)
        
        # create a zip file and store all files into it      
        zipfilehandle = zipfile.ZipFile(zipfilepath, "w")
        zipfilehandle.write(wordfilepath, os.path.basename(str(req.path_info) + '.htm'))
        for image in self.images:
            zipfilehandle.write(image, self.imagesubdir + os.path.basename(image))     
        zipfilehandle.close()
        zip = open(zipfilepath, "rb").read()
        
        # delete temporary folders and files
        self.remove_dir(os.path.join(self.tempdir, self.imagesubdir))
        self.remove_dir(self.tempdir)
        
        # reset image list
        self.images = []
         
        return (zip, 'application/zip')
   
    # remove the xml namespace from the file
    # to be removed once I find out how to override this 
    def xmlns_workaround(self, htmlfilepath):
         # Workaround: Entferne die Namespace-Angabe in der HTML-Datei
        htmlfilehandle = open(htmlfilepath, "r")
        html = htmlfilehandle.read()
        htmlfilehandle.close()
        
        html = re.sub('(<html xmlns="http://www.w3.org/1999/xhtml">)', '<html>', html)
        
        htmlfilehandle = open(htmlfilepath, "w")
        htmlfilehandle.write(html)
        htmlfilehandle.close()
    

    def download_image(self, matchObj):
        imgdir = os.path.join(self.tempdir, self.imagesubdir)
        
        if not os.path.isdir(imgdir):
            os.mkdir(imgdir)
            
        fh, fn = mkstemp(dir = imgdir)
        os.close(fh)
        
        urlretrieve(matchObj.group(1), fn) 
        self.images.append(fn)
        
        return '<img src="%s"' % (self.imagesubdir + os.path.basename(fn))
    
    # for debugging
    def chmod_tmp_dir(self, tempdir):
        os.chmod(tempdir, 0777)
        
        # files
        for f in glob.glob(os.path.join(tempdir ,"*")):
            os.chmod(f, 0777)
    
        
    #removes a directory including all files    
    def remove_dir(self, dir):
        for f in glob.glob(os.path.join(dir, '*')):
            os.unlink(f)
        os.rmdir(dir)
        
        
        

    
    
