
from trac.core import Component, implements
from tracdb import DBComponent
from iface import TracFormDBObserver
import unittest, time, cgi

class TracFormDBComponent(DBComponent):
    applySchema = True
    implements(TracFormDBObserver)

    ###########################################################################
    #
    #   Form update methods.
    #
    ###########################################################################
    def get_tracform_meta(self, src, cursor=None):
        """
        Returns the meta information about a form based on a form_id (int or
        long) or context (string or unicode).
        """
        cursor = self.get_cursor(cursor)
        sql = """
            SELECT  tracform_id, 
                    context, 
                    updater, 
                    updated_on,
                    keep_history,
                    track_fields
            FROM    tracform_forms
            """
        if isinstance(src, basestring):
            sql += """
                WHERE   context = %s
                """
        else:
            sql += """
                WHERE   tracform_id = %s
                """
        form_id = None
        context = None
        if isinstance(src, basestring):
            context = src
        else:
            form_id = src
        return (cursor(sql, src).firstrow or 
                (form_id, context, None, None, None, None))

    def get_tracform_state(self, src, cursor=None):
        cursor = self.get_cursor(cursor)
        sql = """
            SELECT  state
            FROM    tracform_forms
            """
        if isinstance(src, basestring):
            sql += """
                WHERE   context = %s
                """
        else:
            sql += """
                WHERE   tracform_id = %s
                """
        return cursor(sql, src).value

    def save_tracform(self, src, state, updater,
                        base_version=None, keep_history=False,
                        track_fields=False, cursor=None):
        cursor = self.get_cursor(cursor)
        (form_id, context, last_updater, last_updated_on,
            form_keep_history, form_track_fields) = self.get_tracform_meta(src)

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
                        INSERT INTO tracform_forms
                            (context, state, updater, updated_on)
                            VALUES (%s, %s, %s, %s)
                        """, context, state, updater, updated_on) \
                        .last_id('tracform_forms', 'tracform_id')
                else:
                    cursor("""
                        UPDATE  tracform_forms
                        SET     state = %s,
                                updater = %s,
                                updated_on = %s
                        WHERE   tracform_id = %s
                        """, state, updater, updated_on, form_id)
                    if keep_history:
                        cursor("""
                            INSERT INTO tracform_history
                                    (tracform_id, updated_on, 
                                    updater, old_states)
                                    VALUES (%s, %s, %s, %s)
                            """, form_id, last_updated_on,
                                last_updater, old_state)
                if track_fields:
                    # Break down old version and new version.
                    old_fields = cgi.parse_qs(old_state or '')
                    new_fields = cgi.parse_qs(state or '')
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
                            FROM    tracform_fields
                            WHERE   tracform_id = %s
                                AND field = %s""", form_id, field).value:

                            cursor("""
                                UPDATE  tracform_fields
                                    SET updater = %s,
                                        updated_on = %s
                                WHERE   tracform_id = %s
                                    AND field = %s
                                """, updater, updated_on, form_id, field)
                        else:
                            cursor("""
                                INSERT INTO tracform_fields
                                        (tracform_id, field, 
                                        updater, updated_on)
                                VALUES  (%s, %s, %s, %s)
                                """, form_id, field, updater, updated_on)
            else:
                updated_on = last_updated_on
                updater = last_updater
            return ((form_id, context, state, updater, updated_on),
                    (form_id, context, old_state,
                    last_updater, last_updated_on))
        else:
            raise ValueError("Conflict")

    def get_tracform_history(self, src, cursor=None):
        cursor = self.get_cursor(cursor)
        form_id = self.get_tracform_meta(src, cursor=cursor)[0]
        return cursor("""
            SELECT  updater, updated_on, old_states
            FROM    tracform_history
            WHERE   tracform_id = %s
            ORDER   BY updated_on DESC
            """, form_id)

    def get_tracform_fields(self, src, cursor=None):
        cursor = self.get_cursor(cursor)
        form_id = self.get_tracform_meta(src, cursor=cursor)[0]
        return cursor("""
            SELECT  field, updater, updated_on
            FROM    tracform_fields
            WHERE   tracform_id = %s
            """, form_id)

    def get_tracform_fieldinfo(self, src, field, cursor=None):
        cursor = self.get_cursor(cursor)
        form_id = self.get_tracform_meta(src, cursor=cursor)[0]
        return cursor("""
            SELECT  updater, updated_on
            FROM    tracform_fields
            WHERE   tracform_id = %s
                AND field = %s
            """, form_id, field).firstrow or (None, None)

    ###########################################################################
    #
    #   Schema components
    #
    ###########################################################################
    #def dbschema_2008_06_14_0000(self, cursor):
    #    """
    #    This was a simple test for the schema base class.
    #    """

    def db00(self, cursor):
        "Create the major tables."
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
        "Create indices for tracform_forms table."
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
        """
        This was a modify table, but instead removed the data altogether.
        """

    def db03(self, cursor):
        "Create indices for tracform_history table."
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
        "Recreating updated_on index for tracform_forms to be descending."
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
        "Also maintain whether history should me maintained for form."
        cursor("""
            ALTER TABLE tracform_forms
                ADD keep_history INTEGER
            """)

    def db11(self, cursor):
        "Make the context a unique index."
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
        "Track who changes individual fields"
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

if __name__ == '__main__':
    from trac.test import EnvironmentStub
    env = EnvironmentStub()
    db = TracFormDBComponent(env)
    db.upgrade_environment(None)
    updated_on_1 = db.save_tracform('/', 'hello world', 'me')[0][4]
    assert db.get_tracform_state('/') == 'hello world'
    updated_on_2 = \
        db.save_tracform('/', 'ack oop', 'you', updated_on_1)[0][4]
    assert db.get_tracform_state('/') == 'ack oop'
    assert tuple(db.get_tracform_history('/')) == (
        ('me', updated_on_1, 'hello world'),
        )

