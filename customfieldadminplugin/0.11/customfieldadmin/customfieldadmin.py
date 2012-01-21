# -*- coding: utf-8 -*-
"""
Trac WebAdmin plugin for administration of custom fields.

License: BSD

(c) 2005-2012 ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
(c) 2007-2009 ::: www.Optaros.com (.....)
"""

from trac.config import Option
from trac.core import *
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script
from trac.admin.api import IAdminPanelProvider
from api import CustomFields, _


class CustomFieldAdminPage(Component):
    
    implements(ITemplateProvider, IAdminPanelProvider)

    def __init__(self):
        self.env.systeminfo.append(('CustomFieldAdmin',
                __import__('customfieldadmin', ['__version__']).__version__))
        # Be sure to init CustomFields so translations work from first request
        CustomFields(self.env)

    # IAdminPanelProvider methods
    
    def get_admin_panels(self, req):
        if 'TICKET_ADMIN' in req.perm:
            yield ('ticket', _("Ticket System"),
                   'customfields', _("Custom Fields")) 

    def render_admin_panel(self, req, cat, page, customfield):
        req.perm.require('TICKET_ADMIN')
        
        add_script(req, 'customfieldadmin/js/customfieldadmin.js')

        def _customfield_from_req(self, req):
            cfdict = {'name': req.args.get('name','').encode('utf-8'),
                      'label': req.args.get('label','').encode('utf-8'),
                      'type': req.args.get('type','').encode('utf-8'),
                      'value': req.args.get('value','').encode('utf-8'),
                      'options': [x.strip().encode('utf-8') for x in req.args.get('options','').split("\n")],
                      'cols': req.args.get('cols','').encode('utf-8'),
                      'rows': req.args.get('rows','').encode('utf-8'),
                      'order': req.args.get('order', '').encode('utf-8'),
                      'format': req.args.get('format', '').encode('utf-8')}
            return cfdict
        
        cfapi = CustomFields(self.env)
        cfadmin = {} # Return values for template rendering
        
        # Detail view?
        if customfield:
            cf = None
            for a_cf in cfapi.get_custom_fields():
                if a_cf['name'] == customfield:
                    cf = a_cf
                    break
            if not cf:
                raise TracError(_("Custom field %(name)s does not exist.",
                                            name=customfield))
            if req.method == 'POST':
                if req.args.get('save'):
                    cf.update(_customfield_from_req(self, req)) 
                    cfapi.update_custom_field(cf)
                    req.redirect(req.href.admin(cat, page))
                elif req.args.get('cancel'):
                    req.redirect(req.href.admin(cat, page))
            if cf.has_key('options'):
                optional_line = ''
                if cf.get('optional', False):
                    optional_line = "\n\n"
                cf['options'] = optional_line + "\n".join(cf['options'])
            cfadmin['customfield'] = cf
            cfadmin['display'] = 'detail'
        else:
            if req.method == 'POST':
                # Add Custom Field
                if req.args.get('add') and req.args.get('name'):
                    cfdict = _customfield_from_req(self, req)
                    cfapi.update_custom_field(cfdict, create=True)
                    req.redirect(req.href.admin(cat, page))
                         
                # Remove Custom Field
                elif req.args.get('remove') and req.args.get('sel'):
                    sel = req.args.get('sel')
                    sel = isinstance(sel, list) and sel or [sel]
                    if not sel:
                        raise TracError(_("No custom field selected"))
                    for name in sel:
                        cfdict =  {'name': name}
                        cfapi.delete_custom_field(cfdict)
                    req.redirect(req.href.admin(cat, page))

                elif req.args.get('apply'):
                    # Change order
                    order = dict([(key[6:], req.args.get(key)) for key
                                  in req.args.keys()
                                  if key.startswith('order_')])
                    values = dict([(val, True) for val in order.values()])
                    cf = cfapi.get_custom_fields()
                    for cur_cf in cf:
                        cur_cf['order'] = order[cur_cf['name']]
                        cfapi.update_custom_field(cur_cf)
                    req.redirect(req.href.admin(cat, page))

            cf_list = []
            for item in cfapi.get_custom_fields():
                item['href'] = req.href.admin(cat, page, item['name'])
                item['registry'] = ('ticket-custom', 
                                            item['name']) in Option.registry
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
