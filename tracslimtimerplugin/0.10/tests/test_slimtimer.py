
import sys
sys.path = ['..'] + sys.path

import tracslimtimer.slimtimer as ST
import unittest
import datetime
import testconfig

#
# Unit tests for tracslimtimer.slimtimer.SlimTimerSession
#
# The first few tests are very poor as they assume certain tasks have been
# setup in SlimTimer.
#
class SlimTimerTest(unittest.TestCase):

    def setUp(self):
        self.setUpST()

    def setUpST(self):
        if self.__dict__.has_key('st'):
            return

        username = testconfig.get('slimtimer', 'username')
        password = testconfig.get('slimtimer', 'password')
        api_key  = testconfig.get('slimtimer', 'api_key')

        self.st = ST.SlimTimerSession(username, password, api_key)

    def test_basic(self):
        """
        One fat test to cover everything. This should be factored into separate
        tests.
        """

        #
        # We're going to make a task called "New task". If a previous test run
        # failed this task might already exist so let's check and delete it if
        # it does.
        #
        existing = self.st.get_task_by_name("New task")
        if existing:
            existing.delete()
        assert(self.st.get_task_by_name("New task") == None)

        #
        # Ok, create "New task"
        #
        new_task = ST.SlimTimerTask(self.st, "New task")

        #
        # Check the results of the contructor
        #
        self.assertEqual(new_task.id, 0)
        self.assertEqual(new_task.name, "New task")
        self.assertEqual(new_task.complete, False)
        self.assertEqual(new_task.owner, "")
        self.assertEqual(new_task.created_at, 0)
        self.assertEqual(new_task.updated_at, 0)
        self.assertEqual(new_task.completed_on, 0)

        # 
        # Set some test data
        #
        new_task.tags = ['tag 1', 'tag 2']
        new_task.coworkers = ['peter@mail.com', 'paul@mail.com']
        new_task.reporters = ['mary@mail.com']

        #
        # Create in ST
        #
        new_task.update()
        self.assertNotEqual(new_task.id, 0)
        new_task_id = new_task.id

        #
        # Retrieve the task and test
        #
        new_task = None
        result = self.st.get_task_by_id(new_task_id)
        self.assertNotEqual(result, None)
        self.assertEqual(result.id, new_task_id)
        self.assertEqual(result.name, "New task")
        self.assertEqual(result.hours, 0)
        self.assertEqual(result.complete, False)
        self.assertEqual(result.tags, ['tag 1', 'tag 2'])
        self.assertEqual(result.coworkers, ['peter@mail.com', 'paul@mail.com'])
        self.assertEqual(result.reporters, ['mary@mail.com'])
        self.assertEqual(result.owner, testconfig.get('slimtimer', 'username'))
        self.assertNotEqual(result.created_at, 0)
        self.assertNotEqual(result.updated_at, 0)
        self.assertEqual(result.completed_on, 0)

        #
        # Retrieve by name
        #
        result = self.st.get_task_by_name("New task")
        self.assertNotEqual(result, None)
        self.assertEqual(result.id, new_task_id)

        #
        # Delete
        #
        result.delete()
        result = self.st.get_task_by_id(new_task_id)
        self.assertEqual(result, None)
        result = self.st.get_task_by_name("New task")
        self.assertEqual(result, None)

    def test_get_time_entries(self):
        #
        # Our API does not currently provide the possibility of ADDING time
        # entries, only retrieving them. Therefore it's impossible to write an
        # automated test to retrieve entries unless we make assumptions about
        # what entries already exist (i.e. set them up by hand).
        #
        # The following code will work for the developer but noone else.
        #
        """
        entries = self.st.get_time_entries(datetime.datetime(2007,4,11,9),
                                           datetime.datetime(2007,4,11,23))
        self.assertNotEqual(entries, None)
        self.assertEqual(len(entries), 4)
        self.assertEqual(entries[3].id, 770423)
        self.assertEqual(entries[3].start_time,
                         datetime.datetime(2007,4,11,9,30))
        self.assertEqual(entries[3].end_time,
                         datetime.datetime(2007,4,11,11,30))
        self.assertEqual(entries[3].duration, 2 * 60 * 60)
        self.assertEqual(entries[3].tags, 'test tag')
        self.assertEqual(entries[3].comments, 'Did stuff\nDid more stuff')
        self.assertEqual(entries[3].task.id, 126086)
        self.assertEqual(entries[3].task.name, 'Test task')
        """
        pass

if __name__ == '__main__':
    unittest.main()

