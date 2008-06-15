
from trac.core import Component, implements
from tracdb import DBComponent
import unittest, time

class TracFormDBComponent(DBComponent):
    applySchema = True

    ###########################################################################
    #
    #   Form update methods.
    #
    ###########################################################################
    def get_tracform_meta(self, cursor, src):
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
                    keep_history
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
                (form_id, context, None, None, None))

    def get_tracform_state(self, cursor, src):
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

    def save_tracform(self, cursor, src, state, updater,
                        base_version=None, keep_history=True):
        cursor = self.get_cursor(cursor)
        form_id, context, last_updater, last_updated_on, form_keep_history \
            = self.get_tracform_meta(cursor, src)
        if form_keep_history is not None:
            keep_history = form_keep_history
        old_state = self.get_tracform_state(cursor, src)

        if ((base_version is None and last_updated_on is None) or
            (base_version == last_updated_on)):
            if state != old_state:
                updated_on = int(time.time())
                if form_id is None:
                    form_id = cursor("""
                        INSERT INTO tracform_forms
                            (context, state, updater, updated_on)
                            VALUES (%s, %s, %s, %s)
                        """, context, state, updater, updated_on).last_id
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
            else:
                updated_on = last_updated_on
                updater = last_updater
            return ((form_id, context, state, updater, updated_on),
                    (form_id, context, old_state,
                    last_updater, last_updated_on))
        else:
            raise ValueError("Conflict")

    def get_tracform_history(self, cursor, src):
        cursor = self.get_cursor(cursor)
        form_id = self.get_tracform_meta(cursor, src)[0]
        return cursor("""
            SELECT  updater, updated_on, old_states
            FROM    tracform_history
            WHERE   tracform_id = %s
            ORDER   BY updated_on DESC
            """, form_id)

    ###########################################################################
    #
    #   Schema components
    #
    ###########################################################################
    def dbschema_2008_06_14_0000(self, cursor):
        """
        This was a simple test for the schema base class.
        """

    def dbschema_2008_06_15_0000(self, cursor):
        "Create the major tables."
        cursor("""
            CREATE TABLE tracform_forms(
                tracform_id     INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                context         TEXT NOT NULL,
                state           TEXT NOT NULL,
                updater         TEXT NOT NULL,
                updated_on      INTEGER NOT NULL
                )
            """)
        cursor("""
            CREATE TABLE tracform_history(
                tracform_id     INTEGER NOT NULL,
                updated_on      INTEGER NOT NULL,
                updater         TEXT NOT NULL,
                old_states      TEXT NOT NULL
                );
            """)

    def dbschema_2008_06_15_0001(self, cursor):
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

    def dbschema_2008_06_14_0002(self, cursor):
        """
        This was a modify table, but instead removed the data altogether.
        """

    def dbschema_2008_06_15_0003(self, cursor):
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

    def dbschema_2008_06_15_0004(self, cursor):
        "Recreating updated_on index for tracform_forms to be descending."
        cursor("""
            DROP INDEX tracform_forms_updated_on
            """)
        cursor("""
            CREATE INDEX tracform_froms_updated_on
                ON tracform_forms(updated_on DESC)
            """)

    def dbschema_2008_06_15_0010(self, cursor):
        "Also maintain whether history should me maintained for form."
        cursor("""
            ALTER TABLE tracform_forms
                ADD keep_history INTEGER NOT NULL DEFAULT 1
            """)

if __name__ == '__main__':
    from trac.test import EnvironmentStub
    env = EnvironmentStub()
    db = TracFormDBComponent(env)
    db.upgrade_environment(None)
    updated_on_1 = db.save_tracform(None, '/', 'hello world', 'me')[0][4]
    assert db.get_tracform_state(None, '/') == 'hello world'
    updated_on_2 = \
        db.save_tracform(None, '/', 'ack oop', 'you', updated_on_1)[0][4]
    assert db.get_tracform_state(None, '/') == 'ack oop'
    assert tuple(db.get_tracform_history(None, '/')) == (
        ('me', updated_on_1, 'hello world'),
        )

