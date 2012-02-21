# -*- coding: utf-8 -*-

from trac.core import TracError
from trac.wiki.macros import WikiMacroBase
from trac.resource import Resource, get_resource_url
from trac.attachment import Attachment

import os, hashlib
from string import strip

class PdfImgMacro(WikiMacroBase):
    """
    Insert PDFs or vectorgraphics like SVGs as PNG-Image into a wikipage.
    
    requires convert from [http://www.imagemagick.org ImageMagick].
    
    The handling and the parameters are inspired by LaTeX includegraphics. 

    Examples:
    {{{
    [[PdfImg(Book.pdf,width=400,page=100,caption="Page 100 from Book Example")]]
    [[PdfImg(sketch.svg,cache=False)]] 
    }}}
    
    The Location of the file can only be an attachment sofar.
    Locations in the SVN could lead into authentification Problems.
    External Locations means first downloading the resource. 
      
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
   
        self.formatter = formatter
      
        self.parse_arguments(content)
         
        ## Resource to attachment      
        pdfinput=( Attachment(self.env,self.desc) ).path
        #self.env.log.debug("***  Attachment   %r ***", pdfinput )
        
        ## 2. Schritt convert pdf to png like in LatexMacri
        png_filename  = hashlib.sha224(content).hexdigest()
        images_url    = self.formatter.href.chrome('site', '/pfdimg-images')
        images_folder = os.path.join(os.path.normpath(self.env.get_htdocs_dir()), 'pfdimg-images')
        
        if not os.path.exists(images_folder):
            os.mkdir(images_folder)
        
        # generate PNG if not existing
        if  not os.access('%s/%s.png' % (images_folder, png_filename), os.F_OK) or not self.cache:
            # human starts with page 1 ; convert with 0
            if self.page > 0:
                self.page -= 1  
            # example:    convert eingabe.pdf[1] -density 600x600 -resize 800x560 PNG:'ausgabe.png'
            cmd= "convert %s[%s]  -scale %s PNG:'%s/%s.png'" \
                 % (pdfinput , self.page, self.width, images_folder,png_filename)                
            ret = os.system(cmd)
            
            self.env.log.debug("***  convert command   %s ***", cmd )
            
            if ret > 0 :
                raise TracError( ("Cant display %s"%(self.pdfinput)) )
                
            
        #generate HTML-Output
        html_strg   = "\n <!-- PdfImg  %s -->" %(self.url)
        lwitdh=int(self.width) + 3
        html_strg  += '\n <div style="border: 1px solid #CCCCCC;padding: 3px !important;width:%ipx ' \
                    %( lwitdh )
        if self.align:
            html_strg += ' ;float:%s'%(self.align)
        html_strg += ' " ' #close div 
        
        if self.label:
            html_strg +=  ' id="%s"' %(self.label)
        
        displaytitle = self.pdffile        
        html_strg  += '> \n  <a  style="padding:0; border:none" href="%s">\n   <img style="border: 1px solid #CCCCCC;" title="%s" src="%s/%s.png" />\n  </a> ' \
             %(self.rawurl,displaytitle,images_url,png_filename) 
        
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
        url = raw_url = desc = None
        attachment = None
        
        if len(parts) == 3:                 # realm:id:attachment-filename
            realm, id, filename = parts
            attachment = Resource(realm, id).child('attachment', filename)
        elif len(parts) == 2:
            # FIXME: somehow use ResourceSystem.get_known_realms()
            #        ... or directly trac.wiki.extract_link
                    #            from trac.versioncontrol.web_ui import BrowserModule
                    #            try:
                    #                browser_links = [res[0] for res in
                    #                                 BrowserModule(self.env).get_link_resolvers()]
                    #            except Exception:
                    #                browser_links = []
                    #                # TODO what to do with browserlinks...
                    #            if parts[0] in browser_links:   # source:path
                    #                # TODO: use context here as well
                    #                realm, filename = parts
                    #                rev = None
                    #                if '@' in filename:
                    #                    filename, rev = filename.split('@')
                    #                url = self.formatter.href.browser(filename, rev=rev)
                    #                raw_url = self.formatter.href.browser(filename, rev=rev,    format='raw')
                    #                #raw_url = get_resource_url(self.env, attachment, self.formatter.href,     format='raw')
                    #                self.env.log.debug("***  url      %s ***",url)
                    #                self.env.log.debug("***  rawurl   %s ***",browser_links)
                    #
                    #                desc = filespec
                    #            else: # #ticket:attachment or WikiPage:attachment
            if True:   # FIXME: do something generic about shorthand forms...
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
        
        self.url=url
        self.rawurl=raw_url
        self.desc=attachment
        ## END 1. Schritt pdf file ...
