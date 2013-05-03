#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2012 Michael Henke <michael.henke@she.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#

from types import ListType, StringTypes

from trac import __version__ as trac_version
from trac.admin import IAdminPanelProvider
from trac.core import Component, ExtensionPoint, TracError, implements
from trac.env import IEnvironmentSetupParticipant
from trac.perm import (
    PermissionSystem, IPermissionGroupProvider, IPermissionRequestor
)
from trac.ticket.report import ReportModule
from trac.web.chrome import ITemplateProvider
from trac.web.api import ITemplateStreamFilter, IRequestFilter

from genshi.filters import Transformer
from genshi.filters.transform import StreamBuffer
from genshi.input import HTML


class PrivateReports(Component):
    group_providers = ExtensionPoint(IPermissionGroupProvider)

    implements(ITemplateStreamFilter, IEnvironmentSetupParticipant,
               IAdminPanelProvider, ITemplateProvider, IRequestFilter,
               IPermissionRequestor)

    ### IRequestFilter methods

    def pre_process_request(self, req, handler):
        if not isinstance(handler, ReportModule):
            return handler
        report_id = req.args.get('id')
        if not report_id or self._has_permission(req.authname, report_id):
            return handler
        else:
            raise TracError("You don't have permission to access this report",
                            "No Permission")

    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type

    ### ITemplateProvider methods

    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    ### IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('reports', 'Reports',
                   'privatereports', 'Private Reports')

    def render_admin_panel(self, req, cat, page, path_info):
        if page == 'privatereports':
            reports = self._get_reports()
            data = {
                'reports': reports
            }
            if req.method == 'POST':
                report_id = req.args.get('report_id')
                try:
                    report_id = int(report_id)
                except ValueError:
                    req.redirect(self.env.href.admin.reports('privatereports'))
                if req.args.get('add'):
                    new_permission = req.args.get('newpermission')
                    if new_permission is None or \
                            new_permission.isupper() is False:
                        req.redirect(
                            self.env.href.admin.reports('privatereports'))
                    self._insert_report_permission(report_id, new_permission)
                    data['report_permissions'] = \
                        self._get_report_permissions(report_id) or ''
                    data['show_report'] = report_id
                elif req.args.get('remove'):
                    arg_report_permissions = req.args.get('report_permissions')
                    if arg_report_permissions is None:
                        req.redirect(
                            self.env.href.admin.reports('privatereports'))
                    report_permissions = \
                        self._get_report_permissions(report_id)
                    report_permissions = set(report_permissions)
                    to_remove = set()
                    if type(arg_report_permissions) in StringTypes:
                        to_remove.update([arg_report_permissions])
                    elif type(arg_report_permissions) == ListType:
                        to_remove.update(arg_report_permissions)
                    else:
                        req.redirect(
                            self.env.href.admin.reports('privatereports'))
                    report_permissions = report_permissions - to_remove
                    self._alter_report_permissions(report_id,
                                                   report_permissions)
                    data['report_permissions'] = report_permissions or ''
                    data['show_report'] = report_id
                elif req.args.get('show'):
                    report_permissions = \
                        self._get_report_permissions(report_id)
                    data['report_permissions'] = report_permissions or ''
                    data['show_report'] = report_id
            else:
                report_permissions = \
                    self._get_report_permissions(reports[0][1])
                data['report_permissions'] = report_permissions or ''
            return 'admin_privatereports.html', data

    ### IEnvironmentSetupParticipant methods

    def environment_created(self):
        db = self.env.get_db_cnx()
        if self.environment_needs_upgrade(db):
            self.upgrade_environment(db)

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        try:
            cursor.execute('SELECT report_id, permission FROM private_report')
            return False
        except:
            return True

    def upgrade_environment(self, db):
        cursor = db.cursor()
        try:
            cursor.execute('DROP TABLE IF EXISTS private_report')
            db.commit()
        except:
            cursor.connection.rollback()
        try:
            cursor = db.cursor()
            cursor.execute("""
                CREATE TABLE private_report(report_id integer,
                  permission text)""")
            db.commit()
        except:
            cursor.connection.rollback()

    ### ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if not filename == 'report_list.html':
            return stream
        stream_buffer = StreamBuffer()

        from pkg_resources import parse_version
        if parse_version(trac_version) < parse_version('1.0'):
            delimiter = '</tr>'
            selector = '//tbody/tr'
        else:
            delimiter = '</div>'
            selector = '//div[@class="reports"]/div'

        def check_report_permission():
            report_stream = str(stream_buffer)
            reports_raw = report_stream.split(delimiter)
            report_stream = ''
            for row in reports_raw:
                if row is not None and len(row) != 0 and 'View report' in row:
                    # determine the report id
                    s = row.find('/report/')
                    if s == -1:
                        continue
                    e = row.find('\"', s)
                    if e == -1:
                        continue
                    report_id = row[s+len('/report/'):e]
                    if self._has_permission(req.authname, report_id):
                        report_stream += row
                elif 'View report' in row:
                    report_stream += row
            return HTML(report_stream)
        return stream | Transformer(selector) \
            .copy(stream_buffer) \
            .replace(check_report_permission)

    ### IPermissionRequestor methods

    def get_permission_actions(self):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        sql = 'SELECT permission FROM private_report GROUP BY permission'
        cursor.execute(sql)
        report_perms = []
        try:
            for permission in cursor.fetchall():
                report_perms.append(permission[0])
        except:
            pass
        return tuple(report_perms)

    ### Internal methods

    def _has_permission(self, user, report_id):
        report_permissions = self._get_report_permissions(report_id)
        if not report_permissions:
            return True
        perms = PermissionSystem(self.env)
        report_permissions = set(report_permissions)
        user_perm = set(perms.get_user_permissions(user))
        groups = set(self._get_user_groups(user))
        user_perm.update(groups)
        if report_permissions.intersection(user_perm) != set([]):
            return True
        return False

    def _get_user_groups(self, user):
        subjects = set([user])
        for provider in self.group_providers:
            subjects.update(provider.get_permission_groups(user) or [])
        groups = []
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        sql = "SELECT action FROM permission WHERE username = \'%s\'" % (user,)
        cursor.execute(sql)
        rows = cursor.fetchall()
        for action in rows:
            if action[0].isupper():
                groups.append(action[0])
        return groups

    def _get_reports(self):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        sql = 'SELECT title, id FROM report'
        cursor.execute(sql)
        reports = cursor.fetchall()
        return reports

    def _insert_report_permission(self, report_id, permission):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        sql = """
            INSERT INTO private_report(report_id, permission)
            VALUES(%d,'%s')""" % \
            (int(report_id), str(permission))
        cursor.execute(sql)
        db.commit()

    def _alter_report_permissions(self, report_id, permissions):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        sql = 'DELETE FROM private_report WHERE report_id=%d' % \
            (int(report_id),)
        cursor.execute(sql)
        db.commit()
        for permission in permissions:
            self._insert_report_permission(report_id, permission)

    def _get_report_permissions(self, report_id):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        sql = """
            SELECT permission FROM private_report
            WHERE report_id=%d GROUP BY permission""" % (int(report_id),)
        cursor.execute(sql)
        report_perms = []
        try:
            for permission in cursor.fetchall():
                report_perms.append(permission[0])
        except:
            pass
        return report_perms
