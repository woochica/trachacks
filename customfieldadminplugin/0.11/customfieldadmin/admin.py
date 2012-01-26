# -*- coding: utf-8 -*-
"""
Trac WebAdmin plugin for administration of custom fields.

License: BSD

(c) 2005-2012 ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
(c) 2007-2009 ::: www.Optaros.com (.....)
"""

from pkg_resources import resource_filename

from trac.config import Option
from trac.core import *
from trac.web.chrome import ITemplateProvider, add_script, add_warning
from trac.admin.api import IAdminPanelProvider

from customfieldadmin.api import CustomFields, _


class CustomFieldAdminPage(Component):
    
    implements(ITemplateProvider, IAdminPanelProvider)

    def __init__(self):
        # Init CustomFields so translations work from first request
        # FIXME: It actually only works from SECOND request - Trac bug?!
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
            cfield = {'name': req.args.get('name','').encode('utf-8'),
                      'label': req.args.get('label','').encode('utf-8'),
                      'type': req.args.get('type','').encode('utf-8'),
                      'value': req.args.get('value','').encode('utf-8'),
                      'options': [x.strip().encode('utf-8') for x in \
                                    req.args.get('options','').split("\n")],
                      'cols': req.args.get('cols','').encode('utf-8'),
                      'rows': req.args.get('rows','').encode('utf-8'),
                      'order': req.args.get('order', '').encode('utf-8'),
                      'format': req.args.get('format', '').encode('utf-8')}
            return cfield
        
        cf_api = CustomFields(self.env)
        cf_admin = {} # Return values for template rendering
        
        # Detail view?
        if customfield:
            cfield = None
            for a_cfield in cf_api.get_custom_fields():
                if a_cfield['name'] == customfield:
                    cfield = a_cfield
                    break
            if not cfield:
                raise TracError(_("Custom field %(name)s does not exist.",
                                            name=customfield))
            if req.method == 'POST':
                if req.args.get('save'):
                    cfield.update(_customfield_from_req(self, req)) 
                    cf_api.update_custom_field(cfield)
                    req.redirect(req.href.admin(cat, page))
                elif req.args.get('cancel'):
                    req.redirect(req.href.admin(cat, page))
            if cfield.has_key('options'):
                optional_line = ''
                if cfield.get('optional', False):
                    optional_line = "\n\n"
                cfield['options'] = optional_line + "\n".join(cfield['options'])
            cf_admin['cfield'] = cfield
            cf_admin['cf_display'] = 'detail'
        else:
            if req.method == 'POST':
                # Add Custom Field
                if req.args.get('add') and req.args.get('name'):
                    cfield = _customfield_from_req(self, req)
                    cf_api.update_custom_field(cfield, create=True)
                    req.redirect(req.href.admin(cat, page))
                         
                # Remove Custom Field
                elif req.args.get('remove') and req.args.get('sel'):
                    sel = req.args.get('sel')
                    sel = isinstance(sel, list) and sel or [sel]
                    if not sel:
                        raise TracError(_("No custom field selected"))
                    for name in sel:
                        cfield =  {'name': name}
                        cf_api.delete_custom_field(cfield)
                    req.redirect(req.href.admin(cat, page))

                elif req.args.get('apply'):
                    # Change order
                    order = dict([(key[6:], req.args.get(key)) for key
                                  in req.args.keys()
                                  if key.startswith('order_')])
                    cfields = cf_api.get_custom_fields()
                    for current_cfield in cfields:
                        current_cfield['order'] = order[current_cfield['name']]
                        cf_api.update_custom_field(current_cfield)
                    req.redirect(req.href.admin(cat, page))

            cfields = []
            orders_in_use = []
            for item in cf_api.get_custom_fields():
                item['href'] = req.href.admin(cat, page, item['name'])
                item['registry'] = ('ticket-custom', 
                                            item['name']) in Option.registry
                cfields.append(item)
                orders_in_use.append(int(item.get('order')))
            cf_admin['cfields'] = cfields
            cf_admin['cf_display'] = 'list'
            if sorted(orders_in_use) != range(1, len(cfields)+1):
                add_warning(req, _("Custom Fields are not correctly sorted. " \
                         "This may affect appearance when viewing tickets."))

        return ('customfieldadmin.html', cf_admin)
        

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('customfieldadmin', resource_filename(__name__, 'htdocs'))]
