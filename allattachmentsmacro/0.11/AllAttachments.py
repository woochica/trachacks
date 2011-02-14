# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Daan van Etten <daan@stuq.nl>
# All rights reserved.
# This work is licensed under the Creative Commons Attribution-Noncommercial-Share Alike 3.0 License.
# To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ or send 
# a letter to Creative Commons, 171 Second Street, Suite 300, San Francisco, California, 94105, USA.

from trac.wiki.macros import WikiMacroBase, parse_args
from genshi.builder import tag
from trac.util.text import pretty_size
from trac.resource import ResourceNotFound
from trac.attachment import Attachment

revison = "$Rev$"
url = "$URL$"

class AllAttachmentsMacro(WikiMacroBase):
    """Shows all attachments on the Trac site.

       The first argument is the filter for which attachments to show.
       The filter can have the value 'ticket' or 'wiki'. Omitting the filter argument
       shows all attachments.

       Examples:

       {{{
           [[AllAttachments()]]                   # Show all attachments
           [[AllAttachments(ticket)]]             # Show the attachments that are linked to tickets
           [[AllAttachments(wiki)]]               # Show the attachments that are linked to wiki pages
       }}}

       ''Created by Daan van Etten (http://stuq.nl/software/trac/AllAttachmentsMacro)''
    """

    def expand_macro(self, formatter, name, content):
        attachment_type = ""
        if content:
            argv = [arg.strip() for arg in content.split(',')]
            if len(argv) > 0:
                attachment_type = argv[0]

        db = self.env.get_db_cnx()
        if db == None:
           return "No DB connection"
        
        attachmentFormattedList=""

        cursor = db.cursor()

        if attachment_type == None or attachment_type == "":
            cursor.execute("SELECT type,id,filename,size,time,"
                           "description,author,ipnr FROM attachment")
        else:
            cursor.execute("SELECT type,id,filename,size,time,"
                           "description,author,ipnr FROM attachment "
                           "WHERE type=%s", (attachment_type, ))
        
        formatters={"wiki": formatter.href.wiki, "ticket": formatter.href.ticket}
        types={"wiki": "", "ticket": "ticket "}

        return tag.ul(
                      [tag.li(
                          tag.a(filename, href=formatter.href.attachment(type + "/" + id + "/" + filename)), 
                          " (", tag.span(pretty_size(size), title=size), ") - added by ",
                          tag.em(author), " to ",
                          tag.a(types[type] + " " + id, href=formatters[type](id)), " ")
                    for type,id,filename,size,time,description,author,ipnr in cursor if self._has_perm(type, id, filename, formatter.context)])

        return attachmentFormattedList

    def _has_perm(self, parent_realm, parent_id, filename, context):
        try:
            attachment = Attachment(self.env, parent_realm, parent_id, filename)
        except ResourceNotFound:
            return False
        return 'ATTACHMENT_VIEW' in context.req.perm(attachment.resource)
