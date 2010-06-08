#!/usr/bin/python
# -*- coding: utf-8 -*-
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
#
# Based on the main plugins code, Christopher Lenz, and the original DiaView Macro from arkemp.
# Modified for use with Trac 0.11b and now includes Visio and compressed
# file support by robert.martin@arqiva.com


import os
import popen2
import re
import Image


from genshi.builder import tag

from trac.resource import get_resource_url, get_resource_summary
from trac.util.html import escape
from trac.wiki.macros import WikiMacroBase
from trac.attachment import Attachment, AttachmentModule

class DiaVisViewMacro(WikiMacroBase):
    """Embed a Dia as an png image in wiki-formatted text.
    Will automatically convert a Dia to a png file.
    The first argument is the filename, after which
    the horizontal width can be given separated by a comma, as
    can other image parmaeters to position it.  Will now also accept
    vdx format drawings, as well as compressed files.
    Please see the image macro for more details on arguments.
    ''Adapted from the Image.py macro created by Shun-ichi Goto
    <gotoh@taiyo.co.jp>''
    """

    def expand_macro(self, formatter, name, content):
         # args will be null if the macro is called without parenthesis.
        if not content:
            return ''
        # parse arguments
        # we expect the 1st argument to be a filename (filespec)
        args = content.split(',')
        if len(args) == 0:
            raise Exception("No argument.")
        filespec = args[0]

        # style information
        size_re = re.compile('[0-9]+(%|px)?$')
        attr_re = re.compile('(align|border|width|height|alt'
                             '|title|longdesc|class|id|usemap)=(.+)')
        quoted_re = re.compile("(?:[\"'])(.*)(?:[\"'])$")
        attr = {}
        style = {}
        link = ''
        width = None
        for arg in args[1:]:
            arg = arg.strip()
            if size_re.match(arg):
                width = arg
                attr['width'] = arg
                continue
            if arg == 'nolink':
                link = None
                continue
            if arg.startswith('link='):
                val = arg.split('=', 1)[1]
                elt = extract_link(self.env, formatter.context, val.strip())
                link = None
                if isinstance(elt, Element):
                    link = elt.attrib.get('href')
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

        # Got the args now do some processing
        attachment = formatter.resource.child('attachment', filespec)
        realm = formatter.resource.realm
        resource_id     = formatter.resource.id         # The use of "id" could cause a conflict?

        if attachment and 'ATTACHMENT_VIEW' in formatter.perm(attachment):
            url = get_resource_url(self.env, attachment, formatter.href)
            desc = get_resource_summary(self.env, attachment)

        # Includes vdx for use with Visio
        png_url = url.replace(".dia",".png").replace(".vdx",".png")
        dia_attachment = Attachment(self.env, realm, resource_id, filespec)
        dia_path = dia_attachment.path
        dia_filename = dia_attachment.filename
        png_path = dia_path.replace('.dia','.png').replace(".vdx",".png")
        png_filename = dia_filename.replace('.dia','.png').replace(".vdx",".png")
        png_attachment = Attachment(self.env, realm, resource_id, filespec)

        description = 'PNG render of ' + dia_filename

        self.env.log.info('Getting file modification times.')
        try:
            dia_mtime = os.path.getmtime(dia_path)
        except Exception:
            raise Exception('File does not exist: %s', dia_path)

        try:
            png_mtime = os.path.getmtime(png_path)
        except Exception:
            png_mtime = 0
        else:
            try:
                im = Image.open(png_path)
            except Exception, e:
                self.env.log.info('Error checking original png file width for Dia = %s',e)
                raise Exception('Error checking original png file width for Dia.')
            existing_width = im.size[0]


        self.env.log.info('Comparing dia and png file modification times : %s, %s',dia_mtime,dia_mtime)



        if (dia_mtime > png_mtime) or (existing_width != width and width != None):
            try:
                if width:
                  diacmd = 'dia -l --filter=png --size=%dx --export=%s %s' % (int(width), png_path, dia_path)
                else:
                  diacmd = 'dia -l --filter=png --export=%s %s' % (png_path, dia_path)
                self.env.log.info('Running Dia : %s',diacmd)
                f = popen2.Popen4(diacmd)
                lines = []
                while (f.poll() == -1):
                    lines += f.fromchild.readlines()
                    f.wait()
                self.env.log.info('Exiting Dia')
            except Exception, e:
                self.env.log.info('Dia failed with exception= %s',e)
                raise Exception('Dia execution failed.')

            (png_file_size, png_file_time) = os.stat(png_path)[6:8]
            # Based on attachment.py, insert
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            # if an entry exists, based on the columns:- type, id, and filename
            # then it needs updating, rather than creating
            cursor.execute("SELECT filename,description,size,time,author,ipnr "
                       "FROM attachment WHERE type=%s AND id=%s "
                       "AND filename=%s ORDER BY time",
                       (png_attachment.parent_realm, unicode(png_attachment.parent_id), png_filename))
            row = cursor.fetchone()
            if row:
                cursor.execute("UPDATE attachment SET size=%s, time=%s, description=%s, author=%s, ipnr=%s "
                               "WHERE type=%s AND id=%s AND filename=%s",
                               (png_file_size, png_file_time, description, png_attachment.author, png_attachment.ipnr,
                                png_attachment.parent_realm, unicode(png_attachment.parent_id), png_filename))
                self.env.log.info('Updated attachment: %s by %s', png_filename, png_attachment.author)
            else:
                # Insert as new entry
                cursor.execute("INSERT INTO attachment VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                        (png_attachment.parent_realm, png_attachment.parent_id, png_filename,
                            png_file_size, png_file_time, 'PNG render of ' + description,
                            png_attachment.author, png_attachment.ipnr))
                self.env.log.info('New attachment: %s by %s', png_filename, png_attachment.author)

            db.commit()
            cursor.close()
            # This has been included in the hope it would help update
            # the current page being displayed, but no effect noticed
            for listener in AttachmentModule(self.env).change_listeners:
                listener.attachment_added(self)

        for key in ('title', 'alt'):
            if not key in attr:
                attr[key] = description
        if style:
            attr['style'] = '; '.join(['%s:%s' % (k, escape(v))
                                       for k, v in style.iteritems()])
        result = tag.img(src=png_url + "?format=raw", **attr)
        if link is not None:
            result = tag.p(result, href=link or url,
                           style='padding:2; border:none')

        return result
