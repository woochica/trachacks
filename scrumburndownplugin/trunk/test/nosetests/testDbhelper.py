import burndown
import burndown.dbhelper as dbhelper

from trac.core import *
from trac import test as tractest
from nose.tools import *


class testDbHelper():
    def setUp(self):
        self.env = tractest.EnvironmentStub()
        self.db = self.env.get_db_cnx()

    def test_get_milestones(self):
        self.burndown = burndown.BurndownComponent(self.env)
        self.burndown.upgrade_environment(self.db)

        cursor = self.db.cursor()
        milestone = "milestone1"
        due = 0
        completed = 0
        description = "description test milestone"
        started = 0
        cursor.execute("""
            insert into milestone (name, due, completed, description, started)
            values (%s, %s, %s, %s, %s);
            """, (milestone, due, completed, description, started))
        self.db.commit()

        milestones = dbhelper.get_milestones(self.db)

        assert milestone == milestones[0]['name']
        assert due == milestones[0]['due']
        assert completed == milestones[0]['completed']
        assert description == milestones[0]['description']
        assert started == milestones[0]['started']

    def test_get_components(self):
        cursor = self.db.cursor()
        component = "component1"
        cursor.execute("insert into component (name) values (%s);", [component])
        self.db.commit()

        components = dbhelper.get_components(self.db)
        assert component == components[0]['name']

    def test_table_exists(self):
        cursor = self.db.cursor()
        cursor.execute("create table burndown_test (test_name text NOT NULL);")
        self.db.commit()

        assert dbhelper.table_exists(self.db, "burndown_test")
        assert not dbhelper.table_exists(self.db, "burndown_test1")

    def test_table_field_exists(self):
        cursor = self.db.cursor()
        cursor.execute("create table burndown_test (test_name text NOT NULL);")
        self.db.commit()

        assert dbhelper.table_field_exists(self.db, "burndown_test",
                                           "test_name")
        assert not dbhelper.table_field_exists(self.db, "burndown_test",
                                               "test_name1")
        assert not dbhelper.table_field_exists(self.db, "burndown_test1",
                                               "test_name")
