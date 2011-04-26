# -*- coding: utf-8 -*-

import re
import time
import unittest

from trac.core import Component, implements
from trac.resource import Resource, resource_exists
from trac.search.api import search_to_sql

from api import IFormDBObserver, _
from compat import json, parse_qs
from tracdb import DBComponent
from util import resource_from_page, xml_unescape


class FormDBComponent(DBComponent):
    """Provides form update methods and schema components."""

    implements(IFormDBObserver)

    applySchema = True

    # abstract TracForms update methods

    def get_tracform_ids(self, src, cursor=None):
        """Returns all child forms of resource specified by parent realm and
        parent id as a list of tuples (form_id and corresponding subcontext).
        """
        cursor = self.get_cursor(cursor)
        sql = """
            SELECT  id,
                    subcontext
            FROM    forms
            WHERE   realm = %s
                AND resource_id = %s
            """
        ids = []
        results = cursor(sql, *src)
        if results is not None:
            for form_id, subcontext in results:
                ids.append(tuple([int(form_id), subcontext]))
        else:
            raise ResourceNotFound(
                    _("""No data recorded for a TracForms form in
                      %(realm)s:%(parent_id)s
                      """, realm=realm, parent_id=resource_id))
        return ids

    def get_tracform_meta(self, src, cursor=None):
        """
        Returns the meta information about a form based on a form id (int or
        long) or context (parent realm, parent id, TracForms subcontext).
        """
        cursor = self.get_cursor(cursor)
        sql = """
            SELECT  id,
                    realm,
                    resource_id,
                    subcontext,
                    author,
                    time,
                    keep_history,
                    track_fields
            FROM    forms
            """
        if not isinstance(src, int):
            sql += """
                WHERE   realm = %s
                    AND resource_id = %s
                    AND subcontext = %s
                """
        else:
            sql += """
                WHERE   id = %s
                """
        form_id = None
        realm = None
        resource_id = None
        subcontext = None
        if not isinstance(src, int):
            realm, resource_id, subcontext = src
        else:
            form_id = src
            src = tuple([src],)
        return (cursor(sql, *src).firstrow or
            (form_id, realm, resource_id, subcontext, None, None, None, None))

    def get_tracform_state(self, src, cursor=None):
        cursor = self.get_cursor(cursor)
        sql = """
            SELECT  state
            FROM    forms
            """
        if not isinstance(src, int):
            sql += """
                WHERE   realm = %s
                    AND resource_id = %s
                    AND subcontext = %s
                """
        else:
            sql += """
                WHERE   id = %s
                """
            src = tuple([src],)
        return cursor(sql, *src).value

    def save_tracform(self, src, state, author,
                        base_version=None, keep_history=False,
                        track_fields=False, cursor=None):
        cursor = self.get_cursor(cursor)
        (form_id, realm, resource_id, subcontext, last_updater,
            last_updated_on, form_keep_history,
            form_track_fields) = self.get_tracform_meta(src)

        if form_keep_history is not None:
            keep_history = form_keep_history
        old_state = self.get_tracform_state(src)
        if form_track_fields is not None:
            track_fields = form_track_fields

        if base_version is not None:
            base_version = int(base_version or 0)

        if ((base_version is None and last_updated_on is None) or
            (base_version == last_updated_on)):
            if state != old_state:
                updated_on = int(time.time())
                if form_id is None:
                    form_id = cursor("""
                        INSERT INTO forms
                            (realm, resource_id, subcontext,
                            state, author, time)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, realm, resource_id, subcontext,
                        state, author, updated_on) \
                        .last_id('forms', 'id')
                else:
                    cursor("""
                        UPDATE  forms
                        SET     state = %s,
                                author = %s,
                                time = %s
                        WHERE   id = %s
                        """, state, author, updated_on, form_id)
                    if keep_history:
                        cursor("""
                            INSERT INTO forms_history
                                    (id, time, author, old_state)
                                    VALUES (%s, %s, %s, %s)
                            """, form_id, last_updated_on,
                                last_updater, old_state)
                if track_fields:
                    # Break down old version and new version.
                    old_fields = json.loads(old_state or '{}')
                    new_fields = json.loads(state or '{}')
                    updated_fields = []
                    for field, old_value in old_fields.iteritems():
                        if new_fields.get(field) != old_value:
                            updated_fields.append(field)
                    for field in new_fields:
                        if old_fields.get(field) is None:
                            updated_fields.append(field)
                    self.log.debug('UPDATED: ' + str(updated_fields))
                    for field in updated_fields:
                        if cursor("""
                            SELECT  COUNT(*)
                            FROM    forms_fields
                            WHERE   id = %s
                                AND field = %s""", form_id, field).value:

                            cursor("""
                                UPDATE  forms_fields
                                    SET author = %s,
                                        time = %s
                                WHERE   id = %s
                                    AND field = %s
                                """, author, updated_on, form_id, field)
                        else:
                            cursor("""
                                INSERT INTO forms_fields
                                        (id, field, author, time)
                                VALUES  (%s, %s, %s, %s)
                                """, form_id, field, author, updated_on)
            else:
                updated_on = last_updated_on
                author = last_updater
            return ((form_id, realm, resource_id, subcontext, state,
                    author, updated_on),
                    (form_id, realm, resource_id, subcontext, old_state,
                    last_updater, last_updated_on))
        else:
            raise ValueError(_("Conflict"))

    def get_tracform_history(self, src, cursor=None):
        cursor = self.get_cursor(cursor)
        if isinstance(src, int):
            form_id = src
        else:
            form_id = self.get_tracform_meta(src, cursor=cursor)[0]
        return cursor("""
            SELECT  author, time, old_state
            FROM    forms_history
            WHERE   id = %s
            ORDER   BY time DESC
            """, form_id)

    def get_tracform_fields(self, src, cursor=None):
        cursor = self.get_cursor(cursor)
        if isinstance(src, int):
            form_id = src
        else:
            form_id = self.get_tracform_meta(src, cursor=cursor)[0]
        return cursor("""
            SELECT  field, author, time
            FROM    forms_fields
            WHERE   id = %s
            """, form_id)

    def get_tracform_fieldinfo(self, src, field, cursor=None):
        """Retrieve author and time of last change per field."""
        cursor = self.get_cursor(cursor)
        if isinstance(src, int):
            form_id = src
        else:
            form_id = self.get_tracform_meta(src, cursor=cursor)[0]
        return cursor("""
            SELECT  author, time
            FROM    forms_fields
            WHERE   id = %s
                AND field = %s
            """, form_id, field).firstrow or (None, None)

    def reset_tracform(self, src, field=None, author=None, cursor=None):
        """Delete method for all TracForms db tables.

        Note, that we only delete recorded values and history here, while
        the form definition (being part of forms parent resource) is retained.
        """
        # DEVEL: reset of single fields not implemented yet
        cursor = self.get_cursor(cursor)
        form_ids = []
        # collect form_id(s) to reset
        if isinstance(src, int):
            form_ids.append(src)
        elif isinstance(src, tuple) and len(src) == 3:
            if src[-1] is None:
                # no subcontext given, reset all forms of the parent resource
                for form_id in self.get_tracform_ids(src[0], src[1],
                        cursor=cursor):
                    form_ids.append(form_id)
            else:
                form_ids.append(self.get_tracform_meta(src, cursor=cursor)[0])
        for form_id in form_ids:
            cursor("""
                DELETE
                FROM    forms_history
                WHERE   id = %s
                """, form_id)
            cursor("""
                DELETE
                FROM    forms_fields
                WHERE   id = %s
                """, form_id)
            # don't delete basic form reference but save reset as form change
            # to prevent creation of new form id for further retention data
            cursor("""
                UPDATE  forms
                    SET state = %s,
                        author = %s,
                        time = %s
                WHERE   id = %s
                """, '{}', author, int(time.time()), form_id)

    def search_tracforms(self, env, terms, cursor=None):
        """Backend method for TracForms ISearchSource implementation."""
        cursor = self.get_cursor(cursor)
        db = env.get_db_cnx()
        sql, args = search_to_sql(db, ['resource_id', 'subcontext', 'author',
                                       'state', db.cast('id', 'text')], terms)
        return cursor("""
            SELECT id,realm,resource_id,subcontext,state,author,time
            FROM forms
            WHERE %s
            """ % (sql), *args)

    ##########################################################################
    # TracForms schemas

    #def dbschema_2008_06_14_0000(self, cursor):
    #    """This was a simple test for the schema base class."""

    def db00(self, cursor):
        """Create the major tables."""
        cursor("""
            CREATE TABLE tracform_forms(
                tracform_id     INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                context         TEXT NOT NULL,
                state           TEXT NOT NULL,
                updater         TEXT NOT NULL,
                updated_on      INTEGER NOT NULL
                )
            """,
            mysql = """
            CREATE TABLE tracform_forms(
                tracform_id     INT(10) UNSIGNED AUTO_INCREMENT NOT NULL,
                context         VARCHAR(255) NOT NULL,
                state           TEXT NOT NULL,
                updater         VARCHAR(127) NOT NULL,
                updated_on      INTEGER NOT NULL,
                PRIMARY KEY     (tracform_id)
                )
            """)
        cursor("""
            CREATE TABLE tracform_history(
                tracform_id     INTEGER NOT NULL,
                updated_on      INTEGER NOT NULL,
                updater         TEXT NOT NULL,
                old_states      TEXT NOT NULL
                );
            """, mysql="""
            CREATE TABLE tracform_history(
                tracform_id     INTEGER NOT NULL,
                updated_on      INTEGER NOT NULL,
                updater         VARCHAR(127) NOT NULL,
                old_states      TEXT NOT NULL
                );
            """)

    def db01(self, cursor):
        """Create indices for tracform_forms table."""
        cursor("""
            CREATE INDEX tracform_forms_context
                ON tracform_forms(context)
            """)
        cursor("""
            CREATE INDEX tracform_forms_updater
                ON tracform_forms(updater)
            """)
        cursor("""
            CREATE INDEX tracform_forms_updated_on
                ON tracform_forms(updated_on)
            """)

    def db02(self, cursor):
        """This was a modify table, but instead removed the data altogether.
        """

    def db03(self, cursor):
        """Create indices for tracform_history table."""
        cursor("""
            CREATE INDEX tracform_history_tracform_id
                ON tracform_history(tracform_id)
            """)
        cursor("""
            CREATE INDEX tracform_history_updated_on
                ON tracform_history(updated_on DESC)
            """)
        cursor("""
            CREATE INDEX tracform_history_updater
                ON tracform_history(updater)
            """)

    def db04(self, cursor):
        """Recreating updated_on index for tracform_forms to be descending."""
        cursor("""
            DROP INDEX tracform_forms_updated_on
            """, mysql="""
            ALTER TABLE tracform_forms DROP INDEX tracform_forms_updated_on
            """)
        cursor("""
            CREATE INDEX tracform_froms_updated_on
                ON tracform_forms(updated_on DESC)
            """)

    def db10(self, cursor):
        """Also maintain whether history should me maintained for form."""
        cursor("""
            ALTER TABLE tracform_forms
                ADD keep_history INTEGER
            """)

    def db11(self, cursor):
        """Make the context a unique index."""
        cursor("""
            DROP INDEX tracform_forms_context
            """, mysql="""
            ALTER TABLE tracform_forms DROP INDEX tracform_forms_context
            """)
        cursor("""
            CREATE UNIQUE INDEX tracform_forms_context
                ON tracform_forms(context)
            """)

    def db12(self, cursor):
        """Track who changes individual fields."""
        cursor("""
            ALTER TABLE tracform_forms
                ADD track_fields INTEGER
            """)
        cursor("""
            CREATE TABLE tracform_fields(
                tracform_id     INTEGER NOT NULL,
                field           TEXT NOT NULL,
                updater         TEXT NOT NULL,
                updated_on      INTEGER NOT NULL
                )
            """, mysql="""
            CREATE TABLE tracform_fields(
                tracform_id     INTEGER NOT NULL,
                field           VARCHAR(127) NOT NULL,
                updater         VARCHAR(127) NOT NULL,
                updated_on      INTEGER NOT NULL
                )
            """)
        cursor("""
            CREATE UNIQUE INDEX tracform_fields_tracform_id_field
                ON tracform_fields(tracform_id, field)
            """)

    def db13(self, cursor):
        """Convert state serialization type to be more readable.

        Migrate to slicker named major tables and associated indexes too.
        """ 
        cursor("""
            CREATE TABLE forms(
                id              INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                context         TEXT NOT NULL,
                state           TEXT NOT NULL,
                author          TEXT NOT NULL,
                time            INTEGER NOT NULL,
                keep_history    INTEGER,
                track_fields    INTEGER
                )
            """,
            mysql = """
            CREATE TABLE forms(
                id              INT(10) UNSIGNED AUTO_INCREMENT NOT NULL,
                context         VARCHAR(255) NOT NULL,
                state           TEXT NOT NULL,
                author          VARCHAR(127) NOT NULL,
                time            INTEGER NOT NULL,
                keep_history    INTEGER,
                track_fields    INTEGER,
                PRIMARY KEY     (id)
                )
            """)

        forms_columns = ('tracform_id', 'context', 'state', 'updater',
                         'updated_on', 'keep_history', 'track_fields')
        forms_columns_new = ('id', 'context', 'state', 'author',
                             'time', 'keep_history', 'track_fields')

        sql = 'SELECT ' + ', '.join(forms_columns) + ' FROM tracform_forms'
        cursor.execute(sql)
        forms = []
        for row in cursor:
            row = dict(zip(forms_columns_new, row))
            forms.append(row)

        # convert current states serialization
        for form in forms:
            state_new = _url_to_json(form.get('state'))
            if state_new == '{}':
                form['state'] = form.get('state')
            else:
                form['state'] = state_new

        for form in forms:
            fields = form.keys()
            values = form.values()
            sql = "INSERT INTO forms (" + ", ".join(fields) + \
              ") VALUES (" + ", ".join(["%s" for I in xrange(len(fields))]) \
              + ")"
            cursor.execute(sql, *values)

        cursor("""
            DROP INDEX tracform_forms_context
            """, mysql="""
            ALTER TABLE tracform_forms DROP INDEX tracform_forms_context
            """)
        # append common suffix for Trac db indexes to new TracForms indexes
        cursor("""
            CREATE UNIQUE INDEX forms_context_idx
                ON forms(context)
            """)
        cursor("""
            DROP INDEX tracform_forms_updater
            """, mysql="""
            ALTER TABLE tracform_forms DROP INDEX tracform_forms_updater
            """)
        cursor("""
            CREATE INDEX forms_author_idx
                ON forms(author)
            """)
        # remove misspelled index name
        cursor("""
            DROP INDEX tracform_froms_updated_on
            """, mysql="""
            ALTER TABLE tracform_forms DROP INDEX tracform_froms_updated_on
            """)
        cursor("""
            CREATE INDEX forms_time_idx
                ON forms(time DESC)
            """)
        cursor("""
            DROP TABLE tracform_forms
            """)
        # migrate history table
        cursor("""
            CREATE TABLE forms_history
                AS SELECT
                     tracform_id 'id', updated_on 'time',
                     updater 'author', old_states 'old_state'
                FROM tracform_history
            """)

        sql = 'SELECT id,time,old_state FROM forms_history'
        cursor.execute(sql)
        history = []
        for row in cursor:
            row = dict(zip(('id', 'time', 'old_state'), row))
            history.append(row)

        # convert historic states serialization
        for row in history:
            old_state_new = _url_to_json(row.get('old_state'))
            if old_state_new == '{}':
                row['old_state'] = row.get('old_state')
            else:
                row['old_state'] = old_state_new

        for row in history:
            sql = "UPDATE forms_history SET old_state=%s " + \
              "WHERE id=%s AND time=%s"
            cursor.execute(sql, row['old_state'], row['id'], row['time'])

        cursor("""
            DROP INDEX tracform_history_tracform_id
            """, mysql="""
            ALTER TABLE tracform_history DROP INDEX tracform_history_tracform_id
            """)
        cursor("""
            CREATE INDEX forms_history_id_idx
                ON forms_history(id)
            """)
        cursor("""
            DROP INDEX tracform_history_updated_on
            """, mysql="""
            ALTER TABLE tracform_history DROP INDEX tracform_history_updated_on
            """)
        cursor("""
            CREATE INDEX forms_history_time_idx
                ON forms_history(time DESC)
            """)
        cursor("""
            DROP INDEX tracform_history_updater
            """, mysql="""
            ALTER TABLE tracform_history DROP INDEX tracform_history_updater
            """)
        cursor("""
            CREATE INDEX forms_history_author_idx
                ON forms_history(author)
            """)
        cursor("""
            DROP TABLE tracform_history
            """)
        # migrate fields table
        cursor("""
            CREATE TABLE forms_fields
                AS SELECT
                     tracform_id 'id', field, 
                     updater 'author', updated_on 'time'
                FROM tracform_fields
            """)
        cursor("""
            DROP INDEX tracform_fields_tracform_id_field
            """, mysql="""
            ALTER TABLE tracform_fields
                DROP INDEX tracform_fields_tracform_id_field
            """)
        cursor("""
            CREATE UNIQUE INDEX forms_fields_id_field_idx
                ON forms_fields(id, field)
            """)
        cursor("""
            DROP TABLE tracform_fields
            """)
        # remove old TracForms version entry
        cursor("""
            DELETE FROM system WHERE name='TracFormDBComponent:version';
            """)

    def db14(self, cursor):
        """Split context into proper Trac resource descriptors.""" 
        cursor("""
            CREATE TABLE forms_old
                AS SELECT *
                FROM forms
            """)
        cursor("""
            DROP TABLE forms
            """)
        cursor("""
            CREATE TABLE forms(
                id              INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                realm           TEXT NOT NULL,
                resource_id     TEXT NOT NULL,
                subcontext      TEXT,
                state           TEXT NOT NULL,
                author          TEXT NOT NULL,
                time            INTEGER NOT NULL,
                keep_history    INTEGER,
                track_fields    INTEGER
                )
            """,
            mysql = """
            CREATE TABLE forms(
                id              INT(10) UNSIGNED AUTO_INCREMENT NOT NULL,
                realm           VARCHAR(127) NOT NULL,
                resource_id     VARCHAR(255) NOT NULL,
                subcontext      VARCHAR(127),
                state           TEXT NOT NULL,
                author          VARCHAR(127) NOT NULL,
                time            INTEGER NOT NULL,
                keep_history    INTEGER,
                track_fields    INTEGER,
                PRIMARY KEY     (id)
                )
            """)

        forms_columns = ('id', 'context', 'state', 'author',
                         'time', 'keep_history', 'track_fields')

        sql = 'SELECT ' + ', '.join(forms_columns) + ' FROM forms_old'
        cursor.execute(sql)
        forms = []
        for row in cursor:
            row = dict(zip(forms_columns, row))
            # extract realm, resource_id and subcontext from context
            row['realm'], row['resource_id'], row['subcontext'] = \
                _context_to_resource(self.env, row.pop('context'))
            forms.append(row)

        for form in forms:
            fields = form.keys()
            values = form.values()
            sql = "INSERT INTO forms (" + ", ".join(fields) + \
              ") VALUES (" + ", ".join(["%s" for I in xrange(len(fields))]) \
              + ")"
            cursor.execute(sql, *values)

        cursor("""
            CREATE UNIQUE INDEX forms_realm_resource_id_subcontext_idx
                ON forms(realm, resource_id, subcontext)
            """)
        cursor("""
            CREATE INDEX forms_author_idx
                ON forms(author)
            """)
        cursor("""
            CREATE INDEX forms_time_idx
                ON forms(time DESC)
            """)
        cursor("""
            DROP TABLE forms_old
            """)


def _url_to_json(state_url):
    """Convert urlencoded state serial to JSON state serial."""
    state = parse_qs(state_url)
    for name, value in state.iteritems():
        if isinstance(value, (list, tuple)):
            for item in value:
                state[name] = xml_unescape(item)
        else:
            state[name] = xml_unescape(value)
    return json.dumps(state, separators=(',', ':'))

def _context_to_resource(env, context):
    """Find parent realm and resource_id and optional TracForms subcontext.

    Some guesswork is knowingly involved here to finally overcome previous
    potentially ambiguous contexts by distinct resource parameters.
    """
    realm, resource_path = resource_from_page(env, context)
    subcontext = None
    if resource_path is not None:
        # ambiguous: ':' could be part of resource_id or subcontext or
        # the start of subcontext
        segments = re.split(':', resource_path)
        id = ''
        resource_id = None
        while len(segments) > 0:
            id += segments.pop(0)
            # guess: shortest valid resource_id is parent,
            # the rest is a TracForms subcontext
            if resource_exists(env, Resource(realm, id)):
                resource_id = id
                subcontext = ':'.join(segments)
                break
            id += ':'
        # valid resource_id in context NOT FOUND
        if resource_id is None:
            resource_id = resource_path
    else:
        # realm in context NOT FOUND
        resource_id = context
        realm = ''
    return realm, resource_id, subcontext


if __name__ == '__main__':
    from trac.test import EnvironmentStub
    env = EnvironmentStub()
    db = FormDBComponent(env)
    db.upgrade_environment(None)
    updated_on_1 = db.save_tracform('/', 'hello world', 'me')[0][4]
    assert db.get_tracform_state('/') == 'hello world'
    updated_on_2 = \
        db.save_tracform('/', 'ack oop', 'you', updated_on_1)[0][4]
    assert db.get_tracform_state('/') == 'ack oop'
    assert tuple(db.get_tracform_history('/')) == (
        ('me', updated_on_1, 'hello world'),
        )

