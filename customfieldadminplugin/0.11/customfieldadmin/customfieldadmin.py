# -*- coding: utf-8 -*-
"""
Trac WebAdmin plugin for administration of custom fields.

License: BSD

(c) 2005-2008 ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
(c) 2007      ::: www.Optaros.com (.....)
"""

from trac.core import *
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script
from trac.admin.api import IAdminPanelProvider
from api import CustomFields
from trac.util.text import to_unicode


class CustomFieldAdminPage(Component):
    
    implements(ITemplateProvider, IAdminPanelProvider)

    # IAdminPanelProvider methods
    
    def get_admin_panels(self, req):
        if 'TICKET_ADMIN' in req.perm:
            yield ('ticket', 'Ticket System', 'customfields', 'Custom Fields') 

    def render_admin_panel(self, req, cat, page, customfield):
        req.perm.require('TICKET_ADMIN')
        
        add_script(req, 'customfieldadmin/js/CustomFieldAdminPage_actions.js')

        def _customfield_from_req(self, req):
            cfdict = {'name': to_unicode(req.args.get('name')),
                      'label': to_unicode(req.args.get('label')),
                      'type': to_unicode(req.args.get('type')),
                      'value': to_unicode(req.args.get('value')),
                      'options': [x.strip() for x in to_unicode(req.args.get('options')).split("\n")],
                      'cols': to_unicode(req.args.get('cols')),
                      'rows': to_unicode(req.args.get('rows')),
                      'order': req.args.get('order', '')}
            return cfdict
        
        cfapi = CustomFields(self.env)
        cfadmin = {} # Return values for template rendering
        
        # Detail view?
        if customfield:
            exists = [True for cf in cfapi.get_custom_fields(self.env) if cf['name'] == customfield]
            if not exists:
                raise TracError("Custom field %s does not exist." % customfield)
            if req.method == 'POST':
                if req.args.get('save'):
                    cfdict = _customfield_from_req(self, req) 
                    cfapi.update_custom_field(self.env, cfdict)
                    req.redirect(req.href.admin(cat, page))
                elif req.args.get('cancel'):
                    req.redirect(req.href.admin(cat, page))
            currentcf = cfapi.get_custom_fields(self.env, {'name': customfield})
            if currentcf.has_key('options'):
                optional_line = ''
                if currentcf.get('optional', False):
                    optional_line = "\n\n"
                currentcf['options'] = optional_line + "\n".join(currentcf['options'])
            cfadmin['customfield'] = currentcf
            cfadmin['display'] = 'detail'
        else:
            if req.method == 'POST':
                # Add Custom Field
                if req.args.get('add') and req.args.get('name'):
                    cfdict = _customfield_from_req(self, req)
                    cfapi.update_custom_field(self.env, cfdict, create=True)
                    req.redirect(req.href.admin(cat, page))
                         
                # Remove Custom Field
                elif req.args.get('remove') and req.args.get('sel'):
                    sel = req.args.get('sel')
                    sel = isinstance(sel, list) and sel or [sel]
                    if not sel:
                        raise TracError, 'No custom field selected'
                    for name in sel:
                        cfdict =  {'name': name}
                        cfapi.delete_custom_field(self.env, cfdict)
                    req.redirect(req.href.admin(cat, page))

                elif req.args.get('apply'):
                    # Change order
                    order = dict([(key[6:], req.args.get(key)) for key
                                  in req.args.keys()
                                  if key.startswith('order_')])
                    values = dict([(val, True) for val in order.values()])
                    cf = cfapi.get_custom_fields(self.env)
                    for cur_cf in cf:
                        cur_cf['order'] = order[cur_cf['name']]
                        cfapi.update_custom_field(self.env, cur_cf)
                    req.redirect(req.href.admin(cat, page))

            cf_list = []
            for item in cfapi.get_custom_fields(self.env):
                item['href'] = req.href.admin(cat, page, item['name'])
                cf_list.append(item)
            cfadmin['customfields'] = cf_list
            cfadmin['display'] = 'list'

        return ('customfieldadmin.html', {'cfadmin': cfadmin})
        

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('customfieldadmin', resource_filename(__name__, 'htdocs'))]
