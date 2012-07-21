# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 ERCIM
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# Authors: Jean-Guilhem Rouel <jean-guilhem.rouel@ercim.org>
#          Vivien Lacourba <vivien.lacourba@ercim.org>

from genshi.builder import tag
from genshi.filters import Transformer
from trac.core import *
from trac.db import Column, DatabaseManager, Index, Table
from trac.env import IEnvironmentSetupParticipant
from trac.web.api import IRequestFilter, ITemplateStreamFilter

from defaultcc.model import DefaultCC

class DefaultCCAdmin(Component):
    """Allows to setup a default CC list per component through the component
    admin UI.
    """

    implements(IEnvironmentSetupParticipant, ITemplateStreamFilter, IRequestFilter)

    # IEnvironmentSetupParticipant implementation
    SCHEMA = [
        Table('component_default_cc', key='name')[
            Column('name'),
            Column('cc'),
            Index(['name']),
            ]
        ]

    def environment_created(self):
        self._upgrade_db(self.env.get_db_cnx())

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        try:
            cursor.execute("select count(*) from component_default_cc")
            cursor.fetchone()
            return False
        except:
            return True

    def upgrade_environment(self, db):
        self._upgrade_db(db)

    def _upgrade_db(self, db):
        try:
            db_backend, _ = DatabaseManager(self.env)._get_connector()
            cursor = db.cursor()
            for table in self.SCHEMA:
                for stmt in db_backend.to_sql(table):
                    self.log.debug(stmt)
                    cursor.execute(stmt)
                    db.commit()
        except Exception, e:
            self.log.error(e, exc_info=True)
            raise TracError(str(e))

    # IRequestFilter methods
    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type

    def pre_process_request(self, req, handler):
        if 'TICKET_ADMIN' in req.perm and req.method == 'POST' and req.path_info.startswith('/admin/ticket/components'):
            if req.args.get('save'):
                cc = DefaultCC(self.env, req.args.get('old_name'))
                cc.delete()
                cc.name = req.args.get('name')
                cc.cc = req.args.get('defaultcc').strip()
                cc.insert()
            elif req.args.get('remove'):
                if req.args.get('sel'):
                    # If only one component is selected, we don't receive an array, but a string
                    # preventing us from looping in that case :-/
                    if isinstance(req.args.get('sel'), unicode) or isinstance(req.args.get('sel'), str):
                        cc = DefaultCC(self.env, req.args.get('sel'))
                        cc.delete()
                    else:
                        for name in req.args.get('sel'):
                            cc = DefaultCC(self.env, name)
                            cc.delete()
        return handler

    def filter_stream(self, req, method, filename, stream, data):
        if 'TICKET_ADMIN' in req.perm:
            if req.path_info == '/admin/ticket/components' or req.path_info == '/admin/ticket/components/':
                components = data.get('components')
                # 'components' will be None if component with specified name already exists.
                if not components:
                    return stream
                
                default_ccs = DefaultCC.select(self.env)

                stream = stream | Transformer('//table[@id="complist"]/thead/tr') \
                    .append(tag.th('Default CC'))

                filter = Transformer('//table[@id="complist"]/tbody')
                default_comp = self.config.get('ticket', 'default_component')
                for comp in components:
                    if default_comp == comp.name:
                        default_tag = tag.input(type='radio', name='default', value=comp.name, checked='checked')
                    else:
                        default_tag = tag.input(type='radio', name='default', value=comp.name)

                    if comp.name in default_ccs:
                        default_cc = default_ccs[comp.name]
                    else:
                        default_cc = ''

                    filter = filter.append(tag.tr(tag.td(tag.input(type='checkbox', name='sel', value=comp.name), class_='sel'),
                                                  tag.td(tag.a(comp.name, href=req.href.admin('ticket', 'components') + '/' + comp.name), class_='name'),
                                                  tag.td(comp.owner, class_='owner'),
                                                  tag.td(default_tag, class_='default'),
                                                  tag.td(default_cc, class_='defaultcc')))
                return stream | filter

            elif req.path_info.startswith('/admin/ticket/components/') and data.get('component'):
                cc = DefaultCC(self.env, data.get('component').name)
                filter = Transformer('//form[@id="modcomp"]/fieldset/div[@class="buttons"]')
                filter = filter.before(tag.div("Default CC:",
                                               tag.br(),
                                               tag.input(type="text", name="defaultcc", value=cc.cc),
                                               class_="field")) \
                                               .before(tag.input(type='hidden', name='old_name', value=cc.name))
                return stream | filter

        return stream
