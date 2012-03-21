# -*- coding: utf-8 -*-

from trac.core import TracError
from trac.wiki.macros import WikiMacroBase
from trac.resource import Resource, get_resource_url
from trac.attachment import Attachment

import os, hashlib
from string import strip

class PdfImgMacro(WikiMacroBase):
    """
    Insert PDFs or vector graphics like SVGs as PNG-images into a wikipage or ticket.
    
    Requires `convert` from [http://www.imagemagick.org ImageMagick], `convert` may fail on specific files. 
    
    The handling and the parameters are inspired by LaTeX includegraphics and the trac !ImageMacro. 

    Examples:
    {{{
    [[PdfImg(Book.pdf,width=400,page=100,caption="Page 100 from Book Example")]]
    [[PdfImg(source:testpro/drawing.svg@10,width=600,caption="SVG-image from repository in version 10")]]
    [[PdfImg(ticket:1:file.pdf)]]
    }}}
    
    Possible trac links for resource:
    The Location of the file can be an attachment (wikipage, ticket, svn) or a local file (keyword "file:").
    ||= trac link =||= alternatives =||= comment              =||
    || wiki        ||  !JustPageName || Attachment in wikipage ||
    || ticket      ||  !#1           ||                        ||
    || source      ||  browser,repos ||                        ||
    || file        ||                || need configuration `file.prepath`   ||
      
    Parameters:
    ||= Parameter =||= Value                 =||= default =||                         || 
    || `pdffile`   || location of PDF-file    ||           || required                ||
    || page        || Page to display         || 1         || starting with '''1'''   ||  
    || width       || width in pixel          || 600       ||  must be absolute value ||  
    || caption     || Caption under Image     || ''none''  ||                         ||  
    || label       || anchor to link to       ||           ||                         ||
    || || || || ||
    || cache       || build once or each time || True      ||  time consumption or changing vectorgraphics  ||
    || align       || left|right              || nothing   ||                         ||
    
     """
    
    
    ## Parameters inspired by LaTeX-includegraphics
    page   = 1
    width  = 400
    pdffile=None
    caption=None
    label  =None
    
    cache  =True
    align  =None

        
    ##
    ##
    ##
    def expand_macro(self, formatter, name, content):
        if not content:
            return ''
   
        ## Filenames
        self.filenamehash  = hashlib.sha224(content).hexdigest()
        self.images_folder = os.path.join(os.path.normpath(self.env.get_htdocs_dir()), 'pfdimg-images')
       
        # Arguments
        self.formatter = formatter
        self.parse_arguments(content)
         
        images_url = self.formatter.href.chrome('site', '/pfdimg-images')
        
        if not os.path.exists(self.images_folder):
            os.mkdir(self.images_folder)
        
        # generate PNG if not existing
        if  not os.access('%s/%s.png' % (self.images_folder, self.filenamehash), os.F_OK) or not self.cache:
            # human starts with page 1 ; convert with 0
            if self.page > 0:
                self.page -= 1  
            # example:    convert eingabe.pdf[1] -density 600x600 -resize 800x560 PNG:'ausgabe.png'
            cmd= "convert \"%s\"[%s]  -limit area 0  -scale %s PNG:\"%s/%s.png\"" \
                 % (self.pdfinput , self.page, self.width, self.images_folder,self.filenamehash)                
            ret = os.system(cmd)
            
            self.env.log.info("PdfImg..convert command:   %s  %s ***",ret, cmd )
            
            if ret > 0 :
                raise TracError( ("Can't display %s, ImageMagick->convert failed with errorcode=%s , command=%s"%(self.wikilink,ret,cmd)) )
                
            
        # start generate HTML-Output
        html_strg   = "\n <!-- PdfImg  %s -->" %(self.url)
        
        # For Debug purpose
        # html_strg += "\n<br/>[[PdfImg(%s)]]<br/>\n"%(content)
        
        lwitdh=int(self.width) + 3
        html_strg  += '\n <div style="border: 1px solid #CCCCCC;padding: 3px !important;width:%ipx ' \
                    %( lwitdh )
        if self.align:
            html_strg += ' ;float:%s'%(self.align)
        html_strg += ' " ' #close div 
        
        if self.label:
            html_strg +=  ' id="%s"' %(self.label)
        
        # This is the Hover with "wikilink,page"
        if self.page > 1 :
            img_hover ="%s,%s"%(self.wikilink,self.page) 
        else:   
            img_hover ="%s"%(self.wikilink)
                     
        html_strg  += '> \n  <a  style="padding:0; border:none"'
        if self.rawurl: 
            html_strg  += ' href="%s" '%(self.rawurl)
        html_strg  += '>\n    <img style="border: 1px solid #CCCCCC;" title="%s" src="%s/%s.png" />\n  </a> ' \
             %(img_hover,images_url,self.filenamehash) 
        
        if self.caption: 
            html_strg += '\n  <div>%s</div>' %(self.caption) 
            
        html_strg += '\n </div>\n <!-- End PdfImg -->\n'
        return html_strg


    def extract_argument(self,argument):
        """
            input   'arg="aasd asdasd"'
            output  'aasd asdasd'
        """
        ret_strg = argument.split('=', 1)[1]
        # remove quotes
        ret_strg = strip(ret_strg, "\"'")        
        return ret_strg
        
        
    def parse_arguments(self,content):  
        """ parse arguments 
          * see also ImageMacro Parse Arguments 
        """
        # we expect the 1st argument to be a filename (filespec)
        args = content.split(',')
        if len(args) == 0:
            raise Exception("No argument.")
        
        # clean all "LaTeX" - Properties
        self.page   = 1
        self.width  = 400
        self.pdffile=None   
        self.caption=None
        self.label  =None
        self.cache  =True
        self.align  =None
        
        filespec = args[0]
        
        for arg in args[1:]:
            arg = arg.strip()
            if arg.startswith('caption'):
                self.caption = self.extract_argument(arg)            
            if arg.startswith('width'):
                self.width = self.extract_argument(arg)            
            if arg.startswith('page'):
                self.page = int(self.extract_argument(arg))          
            if arg.startswith('label'):
                self.label = self.extract_argument(arg)            
            if arg.startswith('align'):
                self.align = self.extract_argument(arg)            
            if arg.startswith('cache'):
                # strg -> boolean
                strg_cache = self.extract_argument(arg)
                self.cache =  strg_cache.lower()  in ("yes", "true", "t", "1")
                
                
        parts = filespec.split(':')
        partszero_lower=parts[0].lower()
 
        ## Check for special Keys
        if partszero_lower in ('file'): 
            self.parse_file(parts[1])
        else :
            # default trac options
            self.parse_trac(filespec)
    
    
    def parse_trac(self,filespec):
        """
         Parse arguments like in the ImageMacro (trac/wiki/macros.py)
        """
        parts = filespec.split(':')
      
        url = raw_url =  None
        attachment = None  
        if len(parts) == 3:  # realm:id:attachment-filename
            realm, id, filename = parts
            attachment = Resource(realm, id).child('attachment', filename)
        elif len(parts) == 2:
            # TODO howto Access the Subversion / Browser ...
            # FIXME: somehow use ResourceSystem.get_known_realms()
            #        ... or directly trac.wiki.extract_link
            from trac.versioncontrol.web_ui import BrowserModule
            try:
                browser_links = [res[0] for res in
                                 BrowserModule(self.env).get_link_resolvers()]
            except Exception:
                browser_links = []
                # TODO what to do with browserlinks...
            if parts[0] in browser_links:   # source:path
                ##  ['repos', 'export', 'source', 'browser']
                # TODO: use context here as well
                realm, filename = parts
                rev = None
                if '@' in filename:
                    filename, rev = filename.split('@')
                url = self.formatter.href.browser(filename, rev=rev)
                raw_url = self.formatter.href.browser(filename, rev=rev, format='raw')
                
                from trac.versioncontrol.web_ui import get_existing_node
                from trac.versioncontrol import RepositoryManager
                
                if hasattr(RepositoryManager, 'get_repository_by_path'): # Trac 0.12
                    repo = RepositoryManager(self.env).get_repository_by_path(file)[1:3]
                else:
                    repo = RepositoryManager(self.env).get_repository(self.formatter.req.authname)
                obj = get_existing_node(self.formatter.req, repo, filename, rev)
                svn_core_stream=obj.get_content()
                
                # write file to filesystem (needed for convert
                imgname="%s/%s" %(self.images_folder,self.filenamehash)
                f = open( imgname , 'w+')
                f.write( svn_core_stream.read() )
                f.close()
                
                # set standard properties
                # SVN is always cache because it may change...
                self.cache = False
                self.pdfinput = imgname
                self.url=url
                self.rawurl=raw_url
                self.wikilink=filespec 
                return
                    #            else: # #ticket:attachment or WikiPage:attachment
            else : # #ticket:attachment or WikiPage:attachment
                # FIXME: do something generic about shorthand forms...
                realm = None
                id, filename = parts
                if id and id[0] == '#':
                    realm = 'ticket'
                    id = id[1:]
                else:
                    realm = 'wiki'
                if realm:
                    attachment = Resource(realm, id).child('attachment',
                                                           filename)

        elif len(parts) == 1: # it's an attachment of the current resource
            attachment = self.formatter.resource.child('attachment', filespec)
        else:
            raise TracError('No filespec given')
        if attachment and 'ATTACHMENT_VIEW' in self.formatter.perm(attachment):
            url = get_resource_url(self.env, attachment, self.formatter.href)
            raw_url = get_resource_url(self.env, attachment, self.formatter.href,
                                       format='raw')
        
        self.wikilink=filespec
        self.url=url
        self.rawurl=raw_url

        self.pdfinput=( Attachment(self.env,attachment) ).path
        self.env.log.debug("PdfImg..trac-Attachment  %r ***", self.pdfinput )

        
    def parse_file(self,rel_filename):
        """ 
        Display a (internal) file in the file system. 
        
        To use the Resource 'file:' the following configuration must set! 
    {{{
    [pdfimg]
    file.prepath = /relative/entry/directory
    file.preurl  = http://example.com/entrydir
    }}}
        """
        
        file_prepath = self.config.get('pdfimg', 'file.prepath',None)
        url_prepath  = self.config.get('pdfimg', 'file.preurl' ,None)
        
        self.env.log.debug("PdfImg..Location file with file_prepath   %r ***", file_prepath )
        
        if not file_prepath : 
            raise TracError ('Cant use Resource \'file:\' without configuration for pdfimg->file.prepath') 
        
        self.wikilink="file:%s"%(rel_filename)
                    
        if url_prepath: 
            self.rawurl = self.url = '%s/%s'%( url_prepath , rel_filename)
        else:
            self.rawurl = self.url = None
            
        self.pdfinput          = '%s/%s'%( file_prepath, rel_filename)
        
        self.env.log.debug("PdfImg..file:%s -> %s ***",  rel_filename,self.pdfinput )
        return
    
