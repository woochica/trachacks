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

class VersionProjManagerPage(Component):

    implements(IProjManagerPageProvider)

    # IProjManagerPageProvider
    def get_projmanager_pages(self, req):
        if req.perm.has_permission('PROJECT_MANAGER'):
            yield ('project', 'Project System', 'versions', 'Versions')

    def process_projmanager_request(self, req, cat, page, version):
        # Detail view?
        if version:
            ver = ticket.Version(self.env, version)
            if req.method == 'POST':
                if req.args.get('save'):
                    ver.name = req.args.get('name')
                    if req.args.get('time'):
                        try:
                            ver.time =  util.parse_date(req.args.get('time'))
                        except ValueError:
                            ver.time = ""
                    ver.description = req.args.get('description')
                    ver.update()
                    req.redirect(self.env.href.projmanager(cat, page))
                elif req.args.get('cancel'):
                    req.redirect(self.env.href.projmanager(cat, page))

            req.hdf['projmanager.version'] = {
                'name': ver.name,
                'time': ver.time and util.format_datetime(ver.time) or '',
                'description': ver.description
            }
        else:
            if req.method == 'POST':
                # Add Version
                if req.args.get('add') and req.args.get('name'):
                    ver = ticket.Version(self.env)
                    ver.name = req.args.get('name')
                    if req.args.get('time'):
                        ver.time = util.parse_date(req.args.get('time'))
                    if req.args.get('description'):
                        ver.description = req.args.get('description')
                    ver.insert()
                    req.redirect(self.env.href.projmanager(cat, page))
                         
                # Remove versions
                elif req.args.get('remove') and req.args.get('sel'):
                    sel = req.args.get('sel')
                    sel = isinstance(sel, list) and sel or [sel]
                    if not sel:
                        raise TracError, 'No version selected'
                    db = self.env.get_db_cnx()
                    for name in sel:
                        ver = ticket.Version(self.env, name, db=db)
                        ver.delete(db=db)
                    db.commit()
                    req.redirect(self.env.href.projmanager(cat, page))

            req.hdf['projmanager.versions'] = \
                [{'name': version.name,
                  'time': version.time and util.format_datetime(version.time) or '',
                  'href': self.env.href.projmanager(cat, page, version.name)
                 } for version in ticket.Version.select(self.env)]

        return 'projmanager_version.cs', None
