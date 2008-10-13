# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         ImageSvg.py
# Purpose:      The ticket template Trac plugin handler module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
#----------------------------------------------------------------------------

# Adapted from the svgdw.py macro
# 
# Display svg in attachment into the wiki page or ticket.
# 
# The file specification may refer attachments:
#  * 'module:id:file', with module being either 'wiki' or 'ticket',
#    to refer to the attachment named 'file' in the module:id object
#  * 'id:file' same as above, module defaulted to 'wiki' (id can be dir/dir/node)
#  * 'file' to refer to a local attachment named 'file'
#    (but then, this works only from within a wiki page or a ticket).
# 
# Ex.
#   [[svgdw(graph.svg)]]                           # simplest
# 
# You can use image from other page, other ticket or other module.
#   [[svgdw(wiki:OtherPage/SubPage:foo.svg)]]       # another page
#   [[svgdw(ticket:1:bar.svg)]]             # ticket attachment


import os
import re
import string
from trac.attachment import Attachment

def execute(hdf, txt, env):
    # args will be null if the macro is called without parenthesis.
    if not txt:
        return ''
    # parse arguments
    # we expect the 1st argument to be a filename (filespec)
    args = txt.split(',')
    if len(args) == 0:
       raise Exception("No argument.")
    filespec = args[0]
    # parse filespec argument to get module and id if contained.
    parts = filespec.split(':')
    if len(parts) == 3:                 # module:id:attachment
        if parts[0] in ['wiki', 'ticket']:
            module, id, file = parts
            print parts
        else:
            raise Exception("%s module can't have attachments" % parts[0])
    elif len(parts) == 2:               # #ticket:attachment or WikiPage:attachment
        # FIXME: do something generic about shorthand forms...
        id, file = parts
        if id and id[0] == '#':
            module = 'ticket'
            id = id[1:]
        else:
            module = 'wiki'
    elif len(parts) == 1:               # attachment
        file = filespec
        # get current module and id from hdf
        if hdf.getValue('ticket.ts', ''):
            module = "ticket"
        else:
            module = "wiki"

        if module == 'wiki':
            id = hdf.getValue('args.page', 'WikiStart')
        elif module == 'ticket':
            id = hdf['args.id'] # for ticket
        else:
            # limit of use
            raise Exception('Cannot use this macro in %s module' % module)
    else:
        raise Exception( 'No filespec given' )

    try:
        attachment = Attachment(env, module, id, file)
        org_path = attachment.path
        try:
            f = open(org_path, 'r')
            svg = f.readlines()
            f.close()
            svg = "".join(svg).replace('\n', '')
            w = re.search('''width=["']([0-9]+)(.*?)["']''', svg)
            h = re.search('''height=["']([0-9]+)(.*?)["']''', svg)
            (w_val, w_unit) = w.group(1,2)
            (h_val, h_unit) = h.group(1,2)

            unitMapping = {
                "cm": 72 / 2.54,
                "mm": 72 / 25.4,
                "in": 72 / 1,
                "pc": 72 / 6,
            }

            if w_unit in unitMapping.keys():
                w_val = int(float(w_val) * unitMapping[w_unit])
                h_val = int(float(h_val) * unitMapping[w_unit])
                w_unit = "pt"
                h_unit = "pt"


            dimensions = 'width="%(w_val)s%(w_unit)s" height="%(h_val)s%(h_unit)s"' % locals()
        except:
            dimensions = 'width="100%" height="100%"'

        base_url = hdf.getValue('base_url', '')
        project_root = base_url.split("/")[-1]

        data = {
            "project_root": project_root,
            "module": module,
            "id": id,
            "file": file,
            "dimensions": dimensions,
            }
        s = '''
        <div>
        <embed  type="image/svg+xml" 
            style="margin: 0pt; padding: 0pt;"
            src="/%(project_root)s/svg/attachments/%(module)s/%(id)s/%(file)s"  
            %(dimensions)s
            pluginspage="http://www.adobe.com/svg/viewer/install/"> 
        </embed>
        </div>
        ''' % data
        return s
    except:
        return '%s not found' % (filespec)

