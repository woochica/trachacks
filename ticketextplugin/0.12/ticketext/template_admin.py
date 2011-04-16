# -*- coding: utf-8 -*-

from trac import ticket
from trac.core import *
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script
from trac.admin import IAdminPanelProvider
from trac.web.api import ITemplateStreamFilter
from genshi.filters.transform import Transformer
from genshi.template import MarkupTemplate
from api import TicketTemplate
from api import LocaleUtil
from customfieldadmin.api import CustomFields

class TicketTemplateAdmin(Component):
    implements(ITemplateProvider, ITemplateStreamFilter, IAdminPanelProvider)
    
    # ITemplateProvider method
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('ticketext', resource_filename(__name__, 'htdocs'))]

    # ITemplateProvider method
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]


    # ITemplateStreamFilter method
    def filter_stream(self, req, method, filename, stream, data):
        if req.perm.has_permission('TRAC_ADMIN') and filename.startswith('template_admin'):
            script = '\n<script type="text/javascript">'\
                   + 'ticketext.TicketTemplate.setUp(\'' + req.base_path + '\');'\
                   + '</script>\n'
            return stream | Transformer('//div[@id="footer"]').before(MarkupTemplate(script).generate())
        
        return stream

    # IAdminPanelProvider method
    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            # localization
            locale = LocaleUtil().get_locale(req)
            if locale in ['ja', 'ja-JP']:
                yield ('ticket', u'チケットシステム', 'template_admin', u'チケットテンプレート')
            else:
                yield ('ticket', 'Ticket System', 'template_admin', 'Ticket Template')

    # IAdminPanelProvider method
    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.assert_permission('TRAC_ADMIN')
        
        add_script(req, 'ticketext/ticketext.js')
        add_stylesheet(req, 'ticketext/ticketext.css')
        
        # localization
        locale = LocaleUtil().get_locale(req)
        if (locale == 'ja'):
            add_script(req, 'ticketext/ticketext-locale-ja.js')
            page_template = 'template_admin_ja.html'
        else:
            page_template = 'template_admin.html'
        
        if req.method == 'POST':
            self._process_update(req)
            
        page_param = {}
        self._process_read(req, page_param)
        
        return page_template, {'template': page_param}
    
    def _process_read(self, req, page_param):
        ticket_type = req.args.get('type')
        
        ticket_types = [{
            'name'     : type.name,
            'value'    : type.value,
            'selected' : (type.name == ticket_type)
        } for type in ticket.Type.select(self.env)]
        
        # if type isn't selected, it uses the first element.
        if ticket_type == None:
            ticket_type = (ticket_types[0])['name']
        
        template_api = TicketTemplate()
        ticket_template = template_api.get_template_field(self.env, ticket_type)
        
        # check enable customfield
        customfields_api = CustomFields(self.env)
        customfields = customfields_api.get_custom_fields(self.env)
        enable_list = ticket_template['enablefields'].split(',')
        for cf in customfields:
            cf['enable'] = False
            for field in enable_list:
                if (field.strip() == cf['name']):
                    cf['enable'] = True
                    break

        page_param['types']        = ticket_types
        page_param['template']     = ticket_template['template']
        page_param['enablefields'] = ticket_template['enablefields']
        page_param['customfields'] = customfields
        
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
        
        template_api = TicketTemplate()
        template_api.update_template_field(self.env, template_field)
