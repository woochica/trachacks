# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         ttadmin.py
# Purpose:      The ticket template Trac plugin handler module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
#----------------------------------------------------------------------------

from trac.core import *
from trac.util.html import html
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor
from trac.web.chrome import *

from trac.ticket import Milestone, Ticket, TicketSystem, ITicketManipulator

from trac.ticket.web_ui import NewticketModule

from webadmin.web_ui import IAdminPageProvider

from pkg_resources import resource_filename

import os

__all__ = ['TicketTemplateModule']

class TicketTemplateModule(Component):
    ticket_manipulators = ExtensionPoint(ITicketManipulator)
    
    implements(ITemplateProvider, 
               IAdminPageProvider, 
               INavigationContributor, 
               IRequestHandler, 
#               IEnvironmentSetupParticipant, 
               )

    # IEnvironmentSetupParticipant methods

#    def environment_created(self):
#        """Create the `site_newticket.cs` template file in the environment."""
#        if self.env.path:
#            templates_dir = os.path.join(self.env.path, 'templates')
#            if not os.path.exists(templates_dir):
#                os.mkdir(templates_dir)
#            template_name = os.path.join(templates_dir, 'site_newticket.cs')
#            template_file = file(template_name, 'w')
#            template_file.write("""<?cs
#####################################################################
## New ticket prelude - Included directly above the new ticket form
#?>
#""")
#
#    def environment_needs_upgrade(self, db):
#        return False
#
#    def upgrade_environment(self, db):
#        pass


    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'tickettemplate'

    def get_navigation_items(self, req):
        """ hijack the original Trac's 'New Ticket' handler to ticket template
        """
        if not req.perm.has_permission('TICKET_CREATE'):
            return
        yield ('mainnav', 'newticket', 
               html.A(u'New Ticket', href= req.href.tickettemplate()))

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info in ['/tickettemplate' ]


    def process_request(self, req):
        req.perm.assert_permission('TICKET_CREATE')
        
        if req.path_info == '/tickettemplate':
            # setup permission
            really_has_perm = req.perm.has_permission('TICKET_CREATE')
            req.perm.perms['TICKET_CREAT'] = True
            if not really_has_perm:
                del req.perm.perms['TICKET_CREATE']
                
            # call the original new ticket procedure
            template, content_type = NewticketModule(self.env).process_request(req)

            # get all templates for hdf
            tt_list = []
            for tt_name in self._getTicketTypeNames():
                tt_item = {}
                tt_item["name"] = "description_%s" % tt_name
                tt_item["text"] = self._loadTemplateText(tt_name)
                tt_list.append(tt_item)

            req.hdf['tt_list'] = tt_list
            
            # return the cs template
            return 'tt_newticket.cs', 0

    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        self.env.log.info('get_admin_pages')

        if req.perm.has_permission('TRAC_ADMIN'):
            yield 'ticket', 'Ticket', 'tickettemplate', 'Ticket Template'


    def process_admin_request(self, req, cat, page, path_info):
        req.perm.assert_permission('TRAC_ADMIN')
        
        req.hdf['options'] = self._getTicketTypeNames()
        req.hdf['type'] = req.args.get('type')

        if req.method == 'POST':
            tt_file_name = "description_%s.tmpl" % req.args.get('type')
            tt_file_name_default = "description_%s.tmpl" % "default"
            
            tt_file = os.path.join(self.env.path, "templates", tt_file_name)
            tt_file_default = os.path.join(self.env.path, "templates", tt_file_name_default)

            # Load
            if req.args.get('loadtickettemplate'):
                tt_name = req.args.get('type')

                req.hdf['tt_text'] = self._loadTemplateText(tt_name)

            # Save
            elif req.args.get('savetickettemplate'):
                tt_text = req.args.get('description').strip().replace('\r', '')
                tt_name = req.args.get('type')

                self._saveTemplateText(tt_name, tt_text)
                req.hdf['tt_text'] = tt_text

        return 'admin_tickettemplate.cs', None

    # ITemplateProvider
    def get_templates_dirs(self):
        """
            Return the absolute path of the directory containing the provided
            templates
        """
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """
            Return a list of directories with static resources (such as style
            sheets, images, etc.)
    
            Each item in the list must be a `(prefix, abspath)` tuple. The
            `prefix` part defines the path in the URL that requests to these
            resources are prefixed with.
            
            The `abspath` is the absolute path to the directory containing the
            resources on the local file system.
        """
        return [('tt', resource_filename(__name__, 'htdocs'))]
    
    # private methods
    def _getTTFilePath(self, tt_name):
        """ get ticket template file path
        """
        tt_file_name = "description_%s.tmpl" % tt_name
        tt_file = os.path.join(self.env.path, "templates", tt_file_name)
        return tt_file

    def _loadTemplateText(self, tt_name):
        """ load ticket template text from file.
        """
        tt_file         = self._getTTFilePath(tt_name)
        tt_file_default = self._getTTFilePath("default")

        try:
            fp = open(tt_file,'r')
            tt_text = fp.read()
            fp.close()
        except:
            try:
                fp = open(tt_file_default, 'r')
                tt_text = fp.read()
                fp.close()
            except:
                tt_text = ""
                
        return tt_text

    def _saveTemplateText(self, tt_name, tt_text):
        """ save ticket template text to file.
        """
        tt_file = self._getTTFilePath(tt_name)

        try:
            fp = open(tt_file,'w')
        except:
            raise TracError("Can't write ticket template file %s" % tt_file)
        else:
            fp.write(tt_text.encode("utf-8"))
            fp.close()

    def _getTicketTypeNames(self):
        """ get ticket type names
        """
        options = ["default"]

        ticket = Ticket(self.env)
        for field in ticket.fields:
            if field['name'] == 'type':
                options.extend(field['options'])

        return options

