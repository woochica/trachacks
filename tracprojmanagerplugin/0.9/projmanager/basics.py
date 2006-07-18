# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2006 Edgewall Software
# Copyright (C) 2005-2006 Christopher Lenz <cmlenz@gmx.de>
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
# This plugin is based on the WebAdmin plugin, made by Christopher Lenz <cmlenz@gmx.de>
#
# Author: Ricardo Salveti <rsalveti@gmail.com>

from trac.core import *
from projmanager.web_ui import IProjManagerPageProvider


class ProjectManagerPage(Component):

    implements(IProjManagerPageProvider)

    # IProjManagerPageProvider methods

    def get_projmanager_pages(self, req):
        if req.perm.has_permission('PROJECT_MANAGER'):
            yield ('general', 'General', 'project', 'Project Settings')

    def process_projmanager_request(self, req, cat, page, path_info):
        if req.method == "POST":
            self.config.set('project', 'descr', req.args.get('description'))
            self.config.save()
            req.hdf['projmanager.saved_message'] = 'Project description successfully updated.'

        req.hdf['projmanager.project'] = {
            'name': self.config.get('project', 'name'),
            'description': self.config.get('project', 'descr')
        }

        return 'projmanager_basics.cs', None
