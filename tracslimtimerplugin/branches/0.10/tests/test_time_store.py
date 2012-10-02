
import sys
sys.path = ['..'] + sys.path

import tracslimtimer.time_store as TS
import unittest
import datetime
import testconfig

test_tag = "__test_time_store__"

class TimeStoreTest(unittest.TestCase):

    def setUp(self):
        self.setUpStore()

    def setUpStore(self):
        if self.__dict__.has_key('ts'):
            return

        db_host     = testconfig.get('database', 'host')
        db_user     = testconfig.get('database', 'username')
        db_password = testconfig.get('database', 'password')
        db_database = testconfig.get('database', 'database')

        self.ts = TS.TimeStore(host = db_host,
                               user = db_user,
                               password = db_password,
                               database = db_database)

    def test_update_task(self):
        # Grab the connection for our own malicious purposes
        conn = self.ts._TimeStore__conn
        assert conn

        # Check the task we're making doesn't exist
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE src_id = 2")
        self.assertEqual(cursor.rowcount, 0)

        # Insert a new one
        new_id = self.ts.update_task(src_id = 2,
                            name = 'New task',
                            tags = 'tag 1,tag 2',
                            owner = 'brbirtles',
                            created = datetime.datetime(2007,4,11,19,27),
                            updated = datetime.datetime(2007,4,11,19,27,1),
                            time_worked = 1 * 60 * 60,
                            time_estimated = 2 * 60 * 60,
                            completed = 0)

        # The row should exist now
        cursor.execute("SELECT task_id FROM tasks WHERE src_id = 2")
        self.assertEqual(cursor.rowcount, 1)
        self.assert_(new_id > 0)
        self.assertEqual(new_id, cursor.fetchone()[0])

        # Clean up after ourselves
        cursor.execute("DELETE FROM tasks WHERE src_id = 2")
        conn.commit()
        cursor.execute("SELECT * FROM tasks WHERE src_id = 2")
        self.assertEqual(cursor.rowcount, 0)
        cursor.close()

    def test_insert_entry(self):
        # Grab the connection
        conn = self.ts._TimeStore__conn
        assert conn

        # Check the entry we're making doesn't exist
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM times WHERE tags = %s", test_tag)
        self.assertEqual(cursor.rowcount, 0)

        # Insert one
        self.ts.insert_entry(src_id = 3,
                             user = 'testuser',
                             start_time = datetime.datetime(2007,4,11,19,34),
                             end_time = datetime.datetime(2007,4,11,20,32),
                             duration = 1 * 60 * 60,
                             tags = test_tag,
                             comments = 'comment!',
                             task_id = 2)

        # Check it's there
        cursor.execute("SELECT * FROM times WHERE tags = %s",
                       "__test_time_store__")
        self.assertEqual(cursor.rowcount, 1)

        # Tidy up
        cursor.execute("DELETE FROM times WHERE tags = %s", test_tag)
        conn.commit()
        cursor.execute("SELECT * FROM times WHERE tags = %s", test_tag)
        self.assertEqual(cursor.rowcount, 0)
        cursor.close()

    def test_clear_entries(self):
        # Grab the connection, we'll need it later
        conn = self.ts._TimeStore__conn
        assert conn

        # Let's add some entries around the test range: 9am to 5pm
        self.ts.insert_entry(src_id = 3,
                             user = 'testuser',
                             start_time = datetime.datetime(2007,4,11,8,0),
                             end_time = datetime.datetime(2007,4,11,12,0),
                             duration = 4 * 60 * 60,
                             tags = test_tag,
                             comments = 'Start before range -- keep',
                             task_id = 2)
        self.ts.insert_entry(src_id = 4,
                             user = 'testuser',
                             start_time = datetime.datetime(2007,4,11,12,0),
                             end_time = datetime.datetime(2007,4,11,15,0),
                             duration = 3 * 60 * 60,
                             tags = test_tag,
                             comments = 'Wholly within range -- drop',
                             task_id = 3)
        self.ts.insert_entry(src_id = 5,
                             user = 'testuser',
                             start_time = datetime.datetime(2007,4,11,15,0),
                             end_time = datetime.datetime(2007,4,11,18,0),
                             duration = 3 * 60 * 60,
                             tags = test_tag,
                             comments = 
                                'Start within range, end outside -- drop',
                             task_id = 3)
        self.ts.insert_entry(src_id = 6,
                             user = 'testuser',
                             start_time = datetime.datetime(2007,4,11,18,0),
                             end_time = datetime.datetime(2007,4,11,19,0),
                             duration = 1 * 60 * 60,
                             tags = test_tag,
                             comments = 'Totally outside range -- keep',
                             task_id = 3)
        self.ts.insert_entry(src_id = 7,
                             user = 'testuser',
                             start_time = datetime.datetime(2007,4,11,7,0),
                             end_time = datetime.datetime(2007,4,11,20,0),
                             duration = 12 * 60 * 60,
                             tags = test_tag,
                             comments = 'Start before, end after -- keep',
                             task_id = 3)

        # We should now have 5 entries to test
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM times WHERE tags = %s", test_tag)
        self.assertEqual(cursor.rowcount, 5)

        # Clear the range 9am to 5pm
        self.ts.clear_entries('testuser',
                              datetime.datetime(2007,4,11,9,0,0),
                              datetime.datetime(2007,4,11,17,0,0))

        # There should now be only 3 left, 2 were dropped
        cursor.execute(
            "SELECT src_id FROM times WHERE tags = %s ORDER BY src_id",
            test_tag)
        self.assertEqual(cursor.rowcount, 3)

        # Let's check they're the right three
        self.assertEqual(cursor.fetchone()[0], 3)
        self.assertEqual(cursor.fetchone()[0], 6)
        self.assertEqual(cursor.fetchone()[0], 7)

        # Now let's use an indefinite end
        self.ts.clear_entries('testuser', datetime.datetime(2007,4,11,17,30,0))

        # There should now be only 2 left, the last one should have been
        # dropped
        cursor.execute(
            "SELECT src_id FROM times WHERE tags = %s ORDER BY src_id",
            test_tag)
        self.assertEqual(cursor.rowcount, 2)

        # Let's check they're the right two
        self.assertEqual(cursor.fetchone()[0], 3)
        self.assertEqual(cursor.fetchone()[0], 7)

        # Finally, an indefinite start
        self.ts.clear_entries('testuser', None,
                              datetime.datetime(2007,4,11,7,30,0))

        # There should now be only 1 left, the first one should have been
        # dropped
        cursor.execute(
            "SELECT src_id FROM times WHERE tags = %s ORDER BY src_id",
            test_tag)
        self.assertEqual(cursor.rowcount, 1)

        # Let's check we got the right one
        self.assertEqual(cursor.fetchone()[0], 3)

        # Tidy up
        cursor.execute("DELETE FROM times WHERE tags = %s", test_tag)
        conn.commit()
        cursor.execute("SELECT * FROM times WHERE tags = %s", test_tag)
        self.assertEqual(cursor.rowcount, 0)
        cursor.close()


if __name__ == '__main__':
    unittest.main()

