# -*- coding: utf-8 -*-
"""Admin plugin for FieldGroups plugin."""

from pkg_resources import resource_filename

from trac.admin import *
from trac.core import *
from trac.perm import PermissionSystem
from trac.resource import ResourceNotFound
from trac.web.chrome import ITemplateProvider, add_notice, add_stylesheet, add_script
from trac.admin.api import IAdminPanelProvider
from trac.ticket.api import TicketSystem
from trac.util.translation import _, N_, gettext

from api import FieldGroups

class FieldGroupsAdminPanel(Component):

    implements(ITemplateProvider, IAdminPanelProvider)
    required_permissions = ['TRAC_ADMIN', 'TICKET_ADMIN', 'FIELD_GROUP_ADMIN']

    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        if self.check_permissions(req):
            yield ('ticket', 'Ticket System', 'fieldgroups', 'Field Groups') 

    def render_admin_panel(self, req, cat, page, name):
        add_stylesheet(req, 'fieldgroups/css/jquery.dataTables.css')
        add_script(req, 'fieldgroups/js/jquery.dataTables.min.js')
        add_script(req, 'fieldclasses/js/fnGetHiddenNodes.js')

        data = {'view': 'list'}
        label = ['Field Group', 'Field Groups']
        api = FieldGroups(self.env)
        custom_fields = TicketSystem(self.env).get_custom_fields()

        # Detail view?
        if name:
            fieldgroup = api.get_field_group(name)
            if req.method == 'POST':
                if req.args.get('save'):
                    changed = False
                    if fieldgroup['label'] != req.args.get('label'):
                        fieldgroup['label'] = req.args.get('label')
                        changed = True
                    if req.args.get('sel'):
                        sel = req.args.get('sel')
                        if not isinstance(sel, list):
                            sel = [sel]
                        sel = [x.strip().encode('utf-8') for x in sel]
                    else:
                        sel = []
                    if sorted(fieldgroup['fields']) != sorted(sel):
                        fieldgroup['fields'] = sel
                        changed= True
                    if changed:
                        ret = api.update(fieldgroup)
                        add_notice(req, _(ret['msg']))
                    req.redirect(req.href.admin(cat, page))
                elif req.args.get('cancel'):
                    req.redirect(req.href.admin(cat, page))
            data.update({'view': 'detail', 'fieldgroup': fieldgroup, 'fields': custom_fields})

        else:
            if req.method == 'POST':
                # Add enum
                if req.args.get('add') and req.args.get('label'):
                    label = req.args.get('label')
                    if label:
                        fieldgroup = {'label': label, 'order': len(api.get_field_groups()), 'fields': ''}
                        ret = api.insert(fieldgroup)
                        if ret['status']:
                            add_notice(req, _(ret['msg']))
                            req.redirect(req.href.admin(cat, page))
                        else:
                            raise TracError(_(ret['msg']))

                # Remove enums
                elif req.args.get('remove'):
                    sel = req.args.get('sel')
                    if not sel:
                        raise TracError(_('No %s selected') % 'Field Group')
                    if not isinstance(sel, list):
                        sel = [sel]
                    for name in sel:
                        g = api.get_field_group(name)
                        if g:
                            ret = api.delete(g)
                        if not ret['status']:
                            raise TracError(_(ret['msg']))
                    add_notice(req, _('The selected %(field)s have '
                                      'been removed.', field=label[0]))
                    req.redirect(req.href.admin(cat, page))

                # Apply changes
                elif req.args.get('apply'):
                    changed = [False]
                    
                    # Change enum values
                    order = dict([(key[6:], req.args.get(key)) for key
                                  in req.args.keys()
                                  if key.startswith('order_')])
                    values = dict([(val, True) for val in order.values()])
                    if len(order) != len(values):
                        raise TracError(_('Order numbers must be unique'))
                    for g in api.get_field_groups():
                        if order[g['name']] != g['order']:
                            g['order'] = order[g['name']]
                            ret = api.update(g)
                            if not ret['status']:
                                raise TracError(_(ret['msg']))

                    add_notice(req, _('Your changes have been saved.'))
                    req.redirect(req.href.admin(cat, page))

            data = {'fieldgroups': api.get_field_groups(), 'view':'list'}
            for g in data['fieldgroups']:
                g['fields'] = [f for f in custom_fields if f['name'] in g['fields']]
        return ('admin_fieldgroups.html', data)

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('fieldgroups', resource_filename(__name__, 'htdocs'))]

    # internal methods
    def check_permissions(self, req):
        for required in self.required_permissions:
            if required in req.perm:
                return True
        return False
