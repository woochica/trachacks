import re
import sys
import os
import popen2
from trac.config import default_dir
from StringIO import StringIO
from trac.core import *
from trac.wiki.macros import WikiMacroBase
from trac.wiki.macros import ImageMacro
from trac.util.html import escape, html, Markup

class DiaViewMacro(WikiMacroBase):

    def render_macro(self, req, name, content):
        # args will be null if the macro is called without parenthesis.
        if not content:
            return ''
        # parse arguments
        # we expect the 1st argument to be a filename (filespec)
        args = content.split(',')
        if len(args) == 0:
            raise Exception("No argument.")
        filespec = args[0]
        size_re = re.compile('[0-9]+%?$')
        attr_re = re.compile('(align|border|width|height|alt'
                             '|title|longdesc|class|id|usemap)=(.+)')
        quoted_re = re.compile("(?:[\"'])(.*)(?:[\"'])$")
        attr = {}
        style = {}
        nolink = False
        for arg in args[1:]:
            arg = arg.strip()
            if size_re.match(arg):
                # 'width' keyword
                attr['width'] = arg
                continue
            if arg == 'nolink':
                nolink = True
                continue
            if arg in ('left', 'right', 'top', 'bottom'):
                style['float'] = arg
                continue
            match = attr_re.match(arg)
            if match:
                key, val = match.groups()
                m = quoted_re.search(val) # unquote "..." and '...'
                if m:
                    val = m.group(1)
                if key == 'align':
                    style['float'] = val
                elif key == 'border':
                    style['border'] = ' %dpx solid' % int(val);
                else:
                    attr[str(key)] = val # will be used as a __call__ keyword

        # parse filespec argument to get module and id if contained.
        parts = filespec.split(':')
        url = None
        if len(parts) == 3:                 # module:id:attachment
            if parts[0] in ['wiki', 'ticket']:
                module, id, file = parts
            else:
                raise Exception("%s module can't have attachments" % parts[0])
        elif len(parts) == 2:
            from trac.versioncontrol.web_ui import BrowserModule
            try:
                browser_links = [link for link,_ in 
                                 BrowserModule(self.env).get_link_resolvers()]
            except Exception:
                browser_links = []
            if parts[0] in browser_links:   # source:path
                module, file = parts
                rev = None
                if '@' in file:
                    file, rev = file.split('@')
                url = req.href.browser(file, rev=rev)
                raw_url = req.href.browser(file, rev=rev, format='raw')
                desc = filespec
            else: # #ticket:attachment or WikiPage:attachment
                # FIXME: do something generic about shorthand forms...
                id, file = parts
                if id and id[0] == '#':
                    module = 'ticket'
                    id = id[1:]
                elif id == 'htdocs':
                    raw_url = url = req.href.chrome('site', file)
                    desc = os.path.basename(file)
                elif id in ('http', 'https', 'ftp'): # external URLs
                    raw_url = url = desc = id+':'+file
                else:
                    module = 'wiki'
        elif len(parts) == 1:               # attachment
            # determine current object
            # FIXME: should be retrieved from the formatter...
            # ...and the formatter should be provided to the macro
            file = filespec
            module, id = 'wiki', 'WikiStart'
            path_info = req.path_info.split('/',2)
            if len(path_info) > 1:
                module = path_info[1]
            if len(path_info) > 2:
                id = path_info[2]
            if module not in ['wiki', 'ticket']:
                raise Exception('Cannot reference local attachment from here')
        else:
            raise Exception('No filespec given')
        if not url: # this is an attachment
            from trac.attachment import Attachment
            attachment = Attachment(self.env, module, id, file)
            url = attachment.href(req)

            dia_url = attachment.href(req, format='raw')
	    dia_path = attachment.path
	    dia_filename = attachment.filename
            img_url = dia_url.replace(".dia",".png")
	    img_path = dia_path.replace('.dia','.png')
	    img_filename = dia_filename.replace('.dia','.png')

            self.env.log.info('Getting file modification times.')
            #get file modification times
            try:
              dia_mtime = os.path.getmtime(dia_path)
            except Exception:
              raise Exception('File does not exist: %s', dia_path)

            try:
              img_mtime = os.path.getmtime(img_path)
            except Exception:
              img_mtime = 0
                
            self.env.log.info('Comparing dia and png file modification times : %s, %s',dia_mtime,img_mtime)

            # if diagram is newer than image, then regenerate image
            if (dia_mtime > img_mtime):
              try:
		# TODO: read this comment and adjust the command line to taste
		# You should probably use the correct path
		# The options are correct for the 0.96.1, but you may bee to adjust them
                diacmd = 'dia -l --filter=png --export='+img_path+' '+dia_path
                self.env.log.info('Running Dia : %s',diacmd)
	        f = popen2.Popen4(diacmd)
                lines = []
                while (f.poll() == -1):
                  lines += f.fromchild.readlines()
                  f.wait()	
	        #ecode = os.spawnl(os.P_WAIT,'/usr/bin/dia','/usr/bin/dia','-l','--export-to-format=png', '--export='+img_path, dia_path)
                self.env.log.info('Exiting Dia')
              except Exception, e:
                self.env.log.info('Dia failed with exception= %s',e)
                raise Exception('Dia execution failed.')
            try:
	      attachment._fetch(img_filename)
	    except Exception:
              db = self.env.get_db_cnx()
              handle_ta = True
              attachment.size = 0
              attachment.time = 0
              cursor = db.cursor()
              cursor.execute("INSERT INTO attachment "
                             "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                             (attachment.parent_type, attachment.parent_id, img_filename,
                              attachment.size, attachment.time, 'PNG render of a DIA file', attachment.author,
                              attachment.ipnr))
              attachment.filename = img_filename

              self.env.log.info('New attachment: %s', img_filename)

              if handle_ta:
                  db.commit()

            desc = 'JPG render of a DIA file.'
        for key in ['title', 'alt']:
            if desc and not attr.has_key(key):
                attr[key] = desc
        if style:
            attr['style'] = '; '.join(['%s:%s' % (k, escape(v))
                                       for k, v in style.iteritems()])
        result = Markup(html.IMG(src=img_url, **attr)).sanitize()
        #if not nolink:
        #    result = html.A(result, href=url, style='padding:0; border:none')
        return result
