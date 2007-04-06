# Created by Noah Kantrowitz on 2007-04-03.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.

from trac.core import *
from trac.web.chrome import ITemplateProvider
from trac.ticket.api import TicketSystem
from trac.util import sorted
from webadmin.web_ui import IAdminPageProvider

from api import HideValsSystem

class HideValsAdminModule(Component):
    """WebAdmin sub-page for configuring the TracHideVals plugins."""

    implements(IAdminPageProvider, ITemplateProvider)
    
    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('TICKET_ADMIN'):
            for field in TicketSystem(self.env).get_ticket_fields():
                if 'options' in field:
                    yield 'hidevals', 'Hide Values', field['name'], field['label']

    def process_admin_request(self, req, cat, page, path_info):
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        field = dict([(field['name'], field) for field in TicketSystem(self.env).get_ticket_fields()])[page]
        cursor.execute('SELECT sid, value FROM hidevals WHERE field = %s', (field['name'],))
        values = cursor.fetchall()
        enabled = field['name'] not in HideValsSystem(self.env).dont_filter
        
        if req.method == 'POST':
            if req.args.get('add'):
                group = req.args['group']
                value = req.args['value']
                if (group, value) not in values:
                    cursor.execute('INSERT INTO hidevals (sid, field, value) VALUES (%s, %s, %s)', (group, field['name'], value))
                    db.commit()
            elif req.args.get('remove'):
                sel = req.args.getlist('sel')
                for val in sel:
                    group, value = val.split('#', 1)
                    cursor.execute('DELETE FROM hidevals WHERE sid = %s AND field = %s AND value = %s', (group, field['name'], value))
                    db.commit()
            elif req.args.get('toggle'):
                new_val = HideValsSystem(self.env).dont_filter[:]
                if enabled:
                    new_val.append(field['name'])
                else:
                    new_val.remove(field['name']) 
                self.config.set('hidevals', 'dont_filter', ', '.join(sorted(new_val)))
                self.config.save()
                    
            req.redirect(req.href.admin(cat, page))
        
        req.hdf['hidevals.field'] = field
        req.hdf['hidevals.values'] = [{'group': g, 'value': v} for g,v in values]
        req.hdf['hidevals.enabled'] = enabled
        return 'admin_hidevals.cs', None

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
         
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('hidevals', resource_filename(__name__, 'htdocs'))]
