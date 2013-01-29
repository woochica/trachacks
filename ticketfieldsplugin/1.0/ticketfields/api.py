# -*- coding: utf-8 -*-
"""API for Trac TicketFields plugin"""

from trac.core import *
from trac.db import get_column_names
from trac.env import IEnvironmentSetupParticipant
from trac.ticket.api import TicketSystem

class TicketTemplates(Component):
    """TicketTemplates API

    This module also adds the following custom permissions:

      '''ticket_template_modify''':: Permits modifying ticket templates

    """

    implements(IEnvironmentSetupParticipant)

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        cursor.execute("SELECT * FROM sqlite_master WHERE name='ticket_templates' AND type='table'")
        row = cursor.fetchone()
        if not row:
            return True

        # Check for required permissions
        if 'ticket_template_modify' not in self.config['extra-permissions']:
            return True

        # Fall through
        return False

    def upgrade_environment(self, db):
        cursor = db.cursor()

        cursor.execute("SELECT * FROM sqlite_master WHERE name='ticket_templates' AND type='table'")
        row = cursor.fetchone()
        if not row:
            try:
                cursor.execute(self.get_db_schema())
            except Exception, e:
                self.rollback()
                raise e
            db.commit()

        perms = self.config['extra-permissions']
        if 'ticket_template_modify' not in perms:
            perms.set('ticket_template_modify', '')
            self.config.save()

    # internal methods
    def get_ticket_templates(self):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        sql = 'SELECT name, fields FROM ticket_templates ORDER BY name ASC'
        templates = []
        cursor.execute(sql)
        rows = cursor.fetchall()
        if not rows:
            return templates
        cols = get_column_names(cursor)
        fields = [f['name'] for f in TicketSystem(self.env).get_custom_fields()]
        for row in rows:
            tmpl = dict(zip(cols[0:], row[0:]))
            if tmpl['fields']:
                tmpl['fields'] = tmpl['fields'].split(',')
                tmpl['fields'] = [f for f in tmpl['fields'] if f in fields]
            else:
                tmpl['fields'] = []
            templates.append(tmpl)
        return templates

    def get_ticket_template(self, name):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        sql = 'SELECT name, fields FROM ticket_templates WHERE name="%s"' % name
        cursor.execute(sql)
        row = cursor.fetchone()
        if row:
            cols = get_column_names(cursor)
            tmpl = dict(zip(cols[0:], row[0:]))
            if tmpl['fields']:
                tmpl['fields'] = tmpl['fields'].split(',')
                fields = [f['name'] for f in TicketSystem(self.env).get_custom_fields()]
                tmpl['fields'] = [f for f in tmpl['fields'] if f in fields]
            else:
                tmpl['fields'] = []
            return tmpl
        else:
            return None

    def insert(self, tmpl):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        sql = 'SELECT * FROM ticket_templates WHERE name="%s"' % tmpl['name']
        cursor.execute(sql)
        row = cursor.fetchone()
        if row: 
            return {'status': False, 'msg': 'Ticket Template %s already exists!' % tmpl['name']}
        sql = 'INSERT INTO ticket_templates (name, fields) VALUES (%s, %s)'
        params = (tmpl['name'], ','.join(tmpl['fields']))
        try:
            cursor.execute(sql, params)
        except Exception, e:
            self.rollback()
            raise e
        db.commit()
        return {'status': True, 'msg': 'Ticket Template %s created successfully.' % tmpl['name']}

    def update(self, tmpl):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        sql = 'SELECT id FROM ticket_templates WHERE name="%s"' % tmpl['name']
        cursor.execute(sql)
        id = cursor.fetchone()
        if not id: 
            return {'status': False, 'msg': 'Cannot modify Ticket Template %s because it does not exist!' % tmpl['name']}
        try:
            sql = 'UPDATE ticket_templates SET fields="%s" WHERE name="%s"' % (','.join(tmpl['fields']), tmpl['name'])
            cursor.execute(sql)
        except Exception, e:
            self.rollback()
            raise e
        db.commit()
        return {'status': True, 'msg': 'Ticket Template %s updated successfully.'%tmpl['name']}


    def delete(self, tmpl):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        sql = 'DELETE FROM ticket_templates WHERE name="%s"' % tmpl['name']
        try:
            cursor.execute(sql)
        except Exception, e:
            self.rollback()
            return {'status': False, 'msg': e}
        db.commit()
        return {'status': True, 'msg': 'Ticket Template %s deleted successfully.' % tmpl['name']}

    # Internal methods
    def rollback(self):
        db = self.env.get_db_cnx()
        db.rollback()

    # db schema
    def get_db_schema(self):
        schema = """
            CREATE TABLE ticket_templates(
                id                INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                name              TEXT NOT NULL,
                fields            TEXT)"""
        return schema

