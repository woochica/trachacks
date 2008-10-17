# -*- coding: utf-8 -*-

from trac import ticket
from trac.core import *
from webadmin.web_ui import IAdminPageProvider
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script
from trac.util.html import Markup
from api import TicketTemplate
from api import TicketExtUtil
from customfieldadmin.api import CustomFields

class TicketTemplateAdmin(Component):
    implements(ITemplateProvider, IAdminPageProvider)
    
    # ITemplateProvider method
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('ticketext', resource_filename(__name__, 'htdocs'))]

    # ITemplateProvider method
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]


    # IAdminPageProvider method
    def get_admin_pages(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            # localization
            locale = TicketExtUtil(self.env).get_locale(req)
            if locale in ['ja', 'ja-JP']:
                yield ('ticket', 'Ticket System', 'template_admin', u'チケット テンプレート')
            else:
                yield ('ticket', 'Ticket System', 'template_admin', 'Ticket Template')

    # IAdminPageProvider method
    def process_admin_request(self, req, cat, page, path_info):
        req.perm.assert_permission('TRAC_ADMIN')
        
        if req.method == 'POST':
            self._process_update(req)
            
        self._process_read(req)
        
        # localization
        util = TicketExtUtil(self.env)
        locale = util.get_locale(req)
        if locale in ['ja', 'ja-JP']:
            page_template = 'template_admin_ja.cs'
        else:
            page_template = 'template_admin.cs'

        return page_template, None
    
    def _process_read(self, req):
        add_script(req, 'ticketext/jquery.js')
        add_script(req, 'ticketext/ticketext.js')
        footer = req.hdf['project.footer'] + '\n<script type="text/javascript">'\
                                           + 'TicketTemplate.initialize(\'' + req.base_path + '\');'\
                                           + '</script>\n'
        req.hdf['project.footer'] = Markup(footer)
        
        ticket_type = req.args.get('type')
        
        ticket_types = [{
            'name'     : type.name,
            'value'    : type.value,
            'selected' : (type.name == ticket_type)
        } for type in ticket.Type.select(self.env)]
        
        # if type isn't selected, it uses the first element.
        if ticket_type == None:
            ticket_type = (ticket_types[0])['name']
        
        template_api = TicketTemplate(self.env)
        ticket_template = template_api.get_template_field(ticket_type)
        
        # check enable customfield
        customfields_api = CustomFields(self.env)
        customfields = customfields_api.get_custom_fields(self.env)
        enable_list = ticket_template['enablefields'].split(',')
        for cf in customfields:
            cf['enable'] = False
            for field in enable_list:
                if field.strip() == unicode(cf['name'], 'utf-8'):
                    cf['enable'] = True
                    break

        req.hdf['ticketext.template'] = {
            'types'         : ticket_types,
            'template'      : ticket_template['template'],
            'enablefields'  : ticket_template['enablefields'],
            'customfields'  : customfields
        }
        
    def _process_update(self, req):
        ticket_type = req.args.get('type')
        ticket_template = req.args.get('template')
        ticket_cf_enable = req.args.get('cf-enable')
        
        ticket_enablefields = ''
        if (ticket_cf_enable != None):
            if (isinstance(ticket_cf_enable, list)):
                ticket_enablefields = ','.join(ticket_cf_enable)
            else:
                ticket_enablefields = ticket_cf_enable
        
        template_field = {
            'name'         : ticket_type,
            'template'     : ticket_template,
            'enablefields' : ticket_enablefields
        }
        
        template_api = TicketTemplate(self.env)
        template_api.update_template_field(template_field)
