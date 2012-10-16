import re
from trac.core import *
from trac.web.chrome import INavigationContributor, add_script, add_stylesheet, ITemplateProvider
from trac.util import escape, Markup
from pkg_resources import resource_filename
from trac.web.api import IRequestHandler, IRequestFilter

from trac.wiki.macros import WikiMacroBase, parse_args
from genshi.builder import tag
from trac.util.text import pretty_size
from trac.util.datefmt import to_timestamp
from trac.env import IEnvironmentSetupParticipant
import time
import datetime

class FileListInit(Component):
    implements(IEnvironmentSetupParticipant)

    def __init__(self):
        self.version = 0

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        self.upgrade_environment( self.env.get_db_cnx())

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        cursor.execute("SELECT name FROM wiki WHERE name='Files'")
        row = cursor.fetchone()
        if row:
            return False
        else:
            return True

    def upgrade_environment(self, db):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("INSERT INTO wiki VALUES ('Files', 1, '%s', "
                       "'trac', '127.0.0.1', '= Files stored here = \n\n "
                       "[[AllAttachments(wiki, page=Files)]]\n\n"
                       "---- \n\n"
                       "= Files in all wiki pages = \n\n"
                       "[[AllAttachments(wiki)]]',"                      
                       "'', '0')" % (int(time.time()),))
        db.commit()


class FileListPlugin(Component):
    implements(INavigationContributor)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return '/wiki/Files'

    def get_navigation_items(self, req):
        yield 'mainnav', 'filelist', Markup('<a href="%s">Files</a>' % (
                self.env.href.wiki('Files') ) )

class PageCleanup(Component):
    implements(IRequestHandler, IRequestFilter, ITemplateProvider)
    # IRequestHandler methods
    def match_request(self, req):
        return re.match(r'/filelist(?:/(\d+)(/.*))?$', req.path_info)

    def process_request(self, req):
        action = req.args.get('action')
        data = {'action': action}   
        return ('filelist.js', data, 'text/plain')
        req.send('')
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
    def post_process_request(self, req, template, data, content_type):
        if req.path_info.startswith('/wiki/Files'):
            add_script(req, 'js_extras/bgiframe/jquery.bgiframe.pack.js')
            add_stylesheet(req, 'js_extras/jquery-ui/themes/omnipoint/'
                            'jquery-ui-omnipoint.css')
            add_script(req, 'js_extras/jquery-ui/ui/packed/'
                            'ui.core.packed.js')
            add_script(req, 'js_extras/jquery-ui/ui/packed/'
                            'ui.dialog.packed.js')
            add_script(req, 'js_extras/jquery-ui/ui/packed/'
                            'ui.resizable.packed.js')
            add_script(req, 'js_extras/jquery-ui/ui/packed/'
                            'ui.draggable.packed.js')
            add_script(req, 'filelist/js/filelist.js') 
        return template, data, content_type
    # ITemplateProvider methods
    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]
    def get_htdocs_dirs(self):
        return [('filelist', resource_filename(__name__, 'htdocs'))]

class AllAttachmentsMacro(WikiMacroBase):
    """Shows all attachments on the Trac site

       The first argument is the filter for which attachments to show.
       The filter can have the value 'ticket' or 'wiki'. 
       Omitting the filter argument shows all attachments.

       Examples:

       {{{
           [[AllAttachments()]]          # Show all attachments
           [[AllAttachments(ticket)]]    # Show the attachments that 
                                         # are linked to tickets
           [[AllAttachments(wiki)]]      # Show the attachments 
                                         # that are linked to wiki pages

           [[AllAttachments(wiki, page=, order=, sort=)]]
           # page(optional): choose a wiki page to get attachments from
           # order(optional): id (wiki page name), filename, size, time, author
           # sort(optional): ASC/DESC (Ascending or Descending order)

       }}}

       ''Created by Daan van Etten (http://stuq.nl/software/trac/AllAttachmentsMacro)''
    """

    revision = "1.0"
    url = "http://stuq.nl/software/trac/AllAttachments"

    def expand_macro(self, formatter, name, content):
        args, kw = parse_args(content)
        page = kw.get('page', '')
        sort = kw.get('sort', 'DESC')
        order = kw.get('order', 'time')

        self.env.log.error('sort %s, order %s' % (sort, order))

        attachment_type = ""
        wiki_path = ""
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
            cursor.execute("SELECT type,id,filename,size,time,description,"
                           "author,ipnr FROM attachment")

        elif page == None or page == "":
            cursor.execute("SELECT type,id,filename,size,time,description,"
                           "author,ipnr FROM attachment WHERE type=%s ORDER "
                           "BY " + order + " " + sort, (attachment_type,))

        else:
            cursor.execute("SELECT type,id,filename,size,time,description,"
                           "author,ipnr FROM attachment WHERE type=%s and "
                           "id=%s ORDER BY " + order + " " + sort, 
                           (attachment_type, page))

        formatters={"wiki": formatter.href.wiki, 
                    "ticket": formatter.href.ticket}
        types={"wiki": "", "ticket": "ticket "}

        return tag.ul(
                      [tag.li(
                          tag.a(filename, href=formatter.href.attachment(type + "/" + id + "/" + filename)),
                          " (", tag.span(pretty_size(size), title=size), ") - ", tag.em((datetime.datetime.fromtimestamp(time)).ctime()), " - added by ",
                          tag.em(author), " to ",
                          tag.a(types[type] + " " + id, href=formatters[type](id)), " ")
                    for type,id,filename,size,time,description,author,ipnr in cursor])

        return attachmentFormattedList

