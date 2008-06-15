
from trac.core import Component, implements
from tracdb import DBComponent

class TracFormDBComponent(DBComponent):
    applySchema = True

    def dbschema_2008_06_14_0000(self, cursor):
        self.get_cursor(cursor).execute("""
            CREATE TABLE tracform_test(x INTEGER)
            """)

