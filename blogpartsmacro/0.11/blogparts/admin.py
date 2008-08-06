# -*- coding: utf-8 -*-

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.db import Table, Column, Index
from trac.admin import IAdminPanelProvider
from trac.web.chrome import ITemplateProvider
from trac.util.translation import _
import sys
import re
import pkg_resources

import model
from trac.util.datefmt import utc, parse_date, get_date_format_hint, \
                              get_datetime_format_hint
from trac.web.chrome import add_script, add_stylesheet, add_warning, Chrome, \
                            INavigationContributor, ITemplateProvider
from trac.resource import ResourceNotFound
                            
class BlogPartsAdminPanel(Component):
    implements(IAdminPanelProvider,ITemplateProvider)

    _type = 'blogparts'
    _label = ('BlogParts', _('BlogParts'))

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        return [pkg_resources.resource_filename(__name__, 'templates')]
    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'TRAC_ADMIN' in req.perm:
            yield ('blogparts', _('BlogParts'), self._type, self._label[1])

    def render_admin_panel(self, req, cat, page, blogpart):
        req.perm.require('WIKI_ADMIN')
        # Detail view?
        if blogpart:
            ver = model.BlogPart(self.env, blogpart)
            if req.method == 'POST':
                if req.args.get('save'):
                    ver.name = req.args.get('name')
                    if req.args.get('time'):
                        ver.time = parse_date(req.args.get('time'))
                    else:
                        ver.time = None # unset
                    ver.description = req.args.get('description','')
                    ver.header = req.args.get('header','')
                    ver.body = req.args.get('body','')
                    ver.argnum = int(req.args.get('argnum',0))
                    ver.update()
                    req.redirect(req.href.admin(cat, page))
                elif req.args.get('cancel'):
                    req.redirect(req.href.admin(cat, page))

            add_script(req, 'common/js/wikitoolbar.js')
            data = {'view': 'detail', 'blogpart': ver}

        else:
            if req.method == 'POST':
                # Add BlogPart
                if req.args.get('add') and req.args.get('name'):
                    name = req.args.get('name')
                    try:
                        model.BlogPart(self.env, name=name)
                    except ResourceNotFound:
                        ver = model.BlogPart(self.env)
                        ver.name = name
                        if req.args.get('time'):
                            ver.time = parse_date(req.args.get('time'))
                        ver.description = req.args.get('description','')
                        ver.header = req.args.get('header','')
                        ver.body = req.args.get('body','')
                        ver.argnum = int(req.args.get('argnum',0))
                        ver.insert()
                        req.redirect(req.href.admin(cat, page))
                    else:
                        raise TracError(_('BlogPart %s already exists.') % name)
                         
                # Remove blogparts
                elif req.args.get('remove'):
                    sel = req.args.get('sel')
                    if not sel:
                        raise TracError(_('No blogpart selected'))
                    if not isinstance(sel, list):
                        sel = [sel]
                    db = self.env.get_db_cnx()
                    for name in sel:
                        ver = model.BlogPart(self.env, name, db=db)
                        ver.delete(db=db)
                    db.commit()
                    req.redirect(req.href.admin(cat, page))

                # Set default blogpart
                elif req.args.get('apply'):
                    if req.args.get('default'):
                        name = req.args.get('default')
                        self.log.info('Setting default blogpart to %s', name)
                        self.config.set('ticket', 'default_blogpart', name)
                        self.config.save()
                        req.redirect(req.href.admin(cat, page))

            data = {
                'view': 'list',
                'blogparts': model.BlogPart.select(self.env),
                'default': self.config.get('ticket', 'default_blogpart'),
            }

        data.update({
            'datetime_hint': get_datetime_format_hint()
        })
        return 'admin_blogparts.html', data


