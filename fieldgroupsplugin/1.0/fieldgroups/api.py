# -*- coding: utf-8 -*-
"""API for Trac FieldGroups plugin"""

from trac.core import *
from trac.db import get_column_names
from trac.env import IEnvironmentSetupParticipant
from trac.ticket.api import TicketSystem

class FieldGroups(Component):
    """FieldGroups API

    This module also adds the following custom permissions:

      '''field_group_admin''':: Permits administering field groups

    """

    implements(IEnvironmentSetupParticipant)

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        cursor.execute("SELECT * FROM sqlite_master WHERE name='field_groups' AND type='table'")
        row = cursor.fetchone()
        if not row:
            return True

        # Check for required permissions
        if 'field_group_admin' not in self.config['extra-permissions']:
            return True

        # Fall through
        return False

    def upgrade_environment(self, db):
        cursor = db.cursor()

        cursor.execute("SELECT * FROM sqlite_master WHERE name='field_groups' AND type='table'")
        row = cursor.fetchone()
        if not row:
            try:
                cursor.execute(self.get_db_schema())
            except Exception, e:
                self.rollback()
                raise e
            db.commit()

        perms = self.config['extra-permissions']
        if 'field_group_admin' not in perms:
            perms.set('field_group_admin', '')
            self.config.save()

    # internal methods
    def get_field_groups(self):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        sql = 'SELECT id AS "name", label, priority AS "order", fields FROM field_groups ORDER BY priority, label ASC'
        groups = []
        cursor.execute(sql)
        rows = cursor.fetchall()
        if not rows:
            return groups
        cols = get_column_names(cursor)
        fields = [f['name'] for f in TicketSystem(self.env).get_custom_fields()]
        for row in rows:
            group = dict(zip(cols[0:], row[0:]))
            group['name'] = 'fieldgroup_'+str(group['name'])
            if group['fields']:
                group['fields'] = group['fields'].split(',')
                group['fields'] = [f for f in group['fields'] if f in fields]
            groups.append(group)
        return groups

    def get_field_group(self, name):
        # names should always be of the form 'fieldgroup_'+id
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            SELECT id AS "name", label, priority AS "order", fields
            FROM field_groups WHERE id=%s ORDER BY priority, label ASC
            """, (int(name[11:]),))
        row = cursor.fetchone()
        if row:
            cols = get_column_names(cursor)
            group = dict(zip(cols[0:], row[0:]))
            group['name'] = 'fieldgroup_'+str(group['name'])
            if group['fields']:
                group['fields'] = group['fields'].split(',')
                fields = [f['name'] for f in TicketSystem(self.env).get_custom_fields()]
                group['fields'] = [f for f in group['fields'] if f in fields]
            return group
        else:
            return None

    def insert(self, group):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            SELECT * FROM field_groups WHERE label=%s""", (group['label'],))
        row = cursor.fetchone()
        if row: 
            return {'status': False, 'msg': 'Field Group %s already exists!' % group['label']}
        if not group['order']:
            group['order'] = 0
        sql = 'INSERT INTO field_groups (priority, label, fields) VALUES (%s, %s, %s)'
        params = (group['order'], group['label'], ','.join(group['fields']))
        try:
            cursor.execute(sql, params)
        except Exception, e:
            self.rollback()
            return {'status': False, 'msg': e}
        db.commit()
        return {'status': True, 'msg': 'Field Group %s created successfully.' % group['label']}

    def update(self, group):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            SELECT id FROM field_groups WHERE id=%s
            """, (int(group['name'][11:]),))
        id = cursor.fetchone()
        if not id: 
            return {'status': False, 'msg': 'Cannot modify Field Group %s because it does not exist!' % group['label']}
        if 'order' in group:
            group['priority'] = group['order']
            del group['order']
        if 'fields' in group and group['fields']:
            group['fields'] = ','.join(group['fields'])
        try:
            for k,v in group.iteritems():
                if k != 'name':
                    cursor.execute("""
                        UPDATE field_groups SET %s=%%s WHERE id=%%s
                        """ % k, (v or '', id[0]))
        except Exception, e:
            self.rollback()
            return {'status': False, 'msg': e}
        db.commit()
        return {'status': True, 'msg': 'Field Group %s updated successfully.'%group['label']}


    def delete(self, group):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        try:
            cursor.execute("""
                DELETE FROM field_groups WHERE id=%s
                """, (int(group['name'][11:]),))
        except Exception, e:
            self.rollback()
            return {'status': False, 'msg': e}
        db.commit()
        return {'status': True, 'msg': 'Field Group %s deleted successfully.' % group['label']}

    # Internal methods
    def rollback(self):
        db = self.env.get_db_cnx()
        db.rollback()

    # db schema
    def get_db_schema(self):
        schema = """
            CREATE TABLE field_groups(
                id                INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                label             TEXT NOT NULL,
                priority          INTEGER NOT NULL DEFAULT 1,
                fields            TEXT)"""
        return schema

