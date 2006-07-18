# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2006 Edgewall Software
# Copyright (C) 2005 Jonas Borgström <jonas@edgewall.com>
# Copyright (C) 2006 Ricardo Salveti <rsalveti@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.
#
# This plugin is based on the WebAdmin plugin, made by Jonas Borgström <jonas@edgewall.com>
#
# Author: Ricardo Salveti <rsalveti@gmail.com>

from trac import ticket
from trac import util
from trac.core import *
from trac.perm import IPermissionRequestor
from projmanager.web_ui import IProjManagerPageProvider


class ComponentProjManagerPage(Component):

    implements(IProjManagerPageProvider)

    # IProjManagerPageProvider
    def get_projmanager_pages(self, req):
        if req.perm.has_permission('PROJECT_MANAGER'):
            yield ('project', 'Project System', 'components', 'Components')

    def process_projmanager_request(self, req, cat, page, component):
        # Detail view?
        if component:
            comp = ticket.Component(self.env, component)
            if req.method == 'POST':
                if req.args.get('save'):
                    comp.name = req.args.get('name')
                    comp.owner = req.args.get('owner')
                    comp.description = req.args.get('description')
                    comp.update()
                    req.redirect(self.env.href.projmanager(cat, page))
                elif req.args.get('cancel'):
                    req.redirect(self.env.href.projmanager(cat, page))

            req.hdf['projmanager.component'] = {
                'name': comp.name,
                'owner': comp.owner,
                'description': comp.description
            }
        else:
            if req.method == 'POST':
                # Add Component
                if req.args.get('add') and req.args.get('name'):
                    comp = ticket.Component(self.env)
                    comp.name = req.args.get('name')
                    if req.args.get('owner'):
                        comp.owner = req.args.get('owner')
                    if req.args.get('description'):
                        comp.description = req.args.get('description')
                    comp.insert()
                    req.redirect(self.env.href.projmanager(cat, page))

                # Remove components
                elif req.args.get('remove') and req.args.get('sel'):
                    sel = req.args.get('sel')
                    sel = isinstance(sel, list) and sel or [sel]
                    if not sel:
                        raise TracError, 'No component selected'
                    db = self.env.get_db_cnx()
                    for name in sel:
                        comp = ticket.Component(self.env, name, db=db)
                        comp.delete(db=db)
                    db.commit()
                    req.redirect(self.env.href.projmanager(cat, page))

            req.hdf['projmanager.components'] = \
                [{'name': component.name,
                  'owner': component.owner,
                  'href': self.env.href.projmanager(cat, page, component.name)
                 } for component in ticket.Component.select(self.env)]


        if self.config.getbool('ticket', 'restrict_owner'):
            req.hdf['projmanager.owners'] = [username for username, name, email
                                       in self.env.get_known_users()]

        return 'projmanager_component.cs', None
